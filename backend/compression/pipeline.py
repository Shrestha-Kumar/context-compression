"""
Compression pipeline orchestrator.

Coordinates the two-tier compression strategy with a validation gate and
graceful fallback. The single entry point is `compress()`.

Pipeline flow:
    Messages → Constraint Extraction (Tier 1)
             → System prompt prefix built from constraint dict
             → TF-IDF pruning of remaining content (Tier 2)
             → Validation
                 ├─ PASS: return compressed prompt
                 └─ FAIL: fallback to sliding window + constraint prefix
"""

from dataclasses import dataclass, field
from typing import Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage

from backend.agent.state import ConstraintDict
from backend.compression.constraint_extractor import (
    ConstraintExtractor,
    format_constraints_as_prompt,
)
from backend.compression.tfidf_pruner import TFIDFPruner
from backend.compression.validator import CompressionValidator, ValidationResult


# -----------------------------------------------------------------------------
# Result types
# -----------------------------------------------------------------------------

@dataclass
class CompressionResult:
    """Everything the graph node needs after compression runs."""
    # The final prompt to send to the model
    compressed_prompt: str

    # Updated constraint dictionary (may have new extractions)
    updated_constraints: ConstraintDict

    # Telemetry
    raw_tokens: int
    compressed_tokens: int
    ratio: float                  # 1 - (compressed / raw)
    tier_used: str                # "none" | "tier1_only" | "tier1_and_tier2" | "fallback"
    token_scores: list[dict] = field(default_factory=list)
    validation: Optional[ValidationResult] = None


# -----------------------------------------------------------------------------
# Token counting
# -----------------------------------------------------------------------------
# We use a simple heuristic rather than loading the tokenizer here to keep
# this module CPU-only and fast. For Qwen2.5, the rough ratio is 1 token per
# ~3.5 English characters. The exact count happens in inference.py.

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


# -----------------------------------------------------------------------------
# The orchestrator
# -----------------------------------------------------------------------------

class CompressionPipeline:
    """
    Coordinates Tier 1 (constraint extraction) + Tier 2 (TF-IDF pruning)
    + validation + fallback.
    """

    def __init__(
        self,
        pressure_threshold_tokens: int = 1536,  # 75% of 2048
        recent_messages_to_keep: int = 4,       # Always keep last N messages verbatim
        target_ratio: float = 0.60,             # Keep 60% of non-entity tokens
    ):
        self.extractor = ConstraintExtractor()
        self.pruner = TFIDFPruner(target_ratio=target_ratio)
        self.validator = CompressionValidator()
        self.pressure_threshold = pressure_threshold_tokens
        self.recent_to_keep = recent_messages_to_keep

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def compress(
        self,
        messages: list[BaseMessage],
        current_constraints: ConstraintDict,
        user_query: str,
    ) -> CompressionResult:
        """
        Run the full pipeline.

        Args:
            messages: Full conversation history (older → newer).
            current_constraints: Existing constraint dict before this turn.
            user_query: The current user message (included in the prompt).

        Returns:
            CompressionResult containing the final prompt and telemetry.
        """
        # ----- Always run Tier 1: update constraints from all messages -----
        updated_constraints = self.extractor.update(current_constraints, messages)
        constraint_prefix = format_constraints_as_prompt(updated_constraints)

        # ----- Compute raw baseline (no compression) -----
        raw_prompt = self._assemble_raw_prompt(messages, user_query)
        raw_tokens = estimate_tokens(raw_prompt)

        # ----- Decide whether Tier 2 is needed -----
        # If we're below pressure threshold, just inject constraint prefix
        # and return the full history. Tier 1 telemetry but no pruning.
        if raw_tokens <= self.pressure_threshold:
            prompt = self._assemble_with_prefix(
                constraint_prefix, messages, user_query
            )
            tokens = estimate_tokens(prompt)
            return CompressionResult(
                compressed_prompt=prompt,
                updated_constraints=updated_constraints,
                raw_tokens=raw_tokens,
                compressed_tokens=tokens,
                ratio=max(0.0, 1.0 - tokens / max(1, raw_tokens)),
                tier_used="tier1_only",
                token_scores=[],
            )

        # ----- Tier 2: TF-IDF pruning on middle messages -----
        # Keep last N messages verbatim. Prune older messages aggressively.
        recent, older = self._split_messages(messages)
        pruned_history, token_scores = self._prune_messages(older)

        compressed_prompt = self._assemble_prompt_parts(
            constraint_prefix=constraint_prefix,
            history_text=pruned_history,
            recent_messages=recent,
            user_query=user_query,
        )

        # ----- Validate -----
        validation = self.validator.validate(compressed_prompt, updated_constraints)

        if not validation.passed:
            # Fallback: simple sliding window + constraint prefix
            fallback_prompt = self._fallback_sliding_window(
                constraint_prefix, messages, user_query
            )
            fallback_tokens = estimate_tokens(fallback_prompt)
            return CompressionResult(
                compressed_prompt=fallback_prompt,
                updated_constraints=updated_constraints,
                raw_tokens=raw_tokens,
                compressed_tokens=fallback_tokens,
                ratio=max(0.0, 1.0 - fallback_tokens / max(1, raw_tokens)),
                tier_used="fallback",
                token_scores=token_scores,
                validation=validation,
            )

        compressed_tokens = estimate_tokens(compressed_prompt)
        return CompressionResult(
            compressed_prompt=compressed_prompt,
            updated_constraints=updated_constraints,
            raw_tokens=raw_tokens,
            compressed_tokens=compressed_tokens,
            ratio=max(0.0, 1.0 - compressed_tokens / max(1, raw_tokens)),
            tier_used="tier1_and_tier2",
            token_scores=token_scores,
            validation=validation,
        )

    # ------------------------------------------------------------------
    # Prompt assembly helpers
    # ------------------------------------------------------------------

    def _assemble_raw_prompt(self, messages: list[BaseMessage], user_query: str) -> str:
        """Baseline: what the prompt would be with zero compression."""
        parts = [self._format_message(m) for m in messages]
        parts.append(f"User: {user_query}")
        return "\n".join(parts)

    def _assemble_with_prefix(
        self,
        prefix: str,
        messages: list[BaseMessage],
        user_query: str,
    ) -> str:
        """Tier 1 only: full history + constraint prefix."""
        lines = []
        if prefix:
            lines.append(prefix)
            lines.append("")
        for m in messages:
            lines.append(self._format_message(m))
        lines.append(f"User: {user_query}")
        return "\n".join(lines)

    def _assemble_prompt_parts(
        self,
        constraint_prefix: str,
        history_text: str,
        recent_messages: list[BaseMessage],
        user_query: str,
    ) -> str:
        """Full Tier 2 assembly: prefix + pruned history + recent + query."""
        lines = []
        if constraint_prefix:
            lines.append(constraint_prefix)
            lines.append("")
        if history_text:
            lines.append("[COMPRESSED HISTORY]")
            lines.append(history_text)
            lines.append("")
        lines.append("[RECENT TURNS]")
        for m in recent_messages:
            lines.append(self._format_message(m))
        lines.append(f"User: {user_query}")
        return "\n".join(lines)

    def _format_message(self, msg: BaseMessage) -> str:
        """Convert a message to a single display line."""
        role = {
            HumanMessage: "User",
            AIMessage: "Assistant",
            SystemMessage: "System",
            ToolMessage: "Tool",
        }.get(type(msg), "Message")
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        return f"{role}: {content}"

    # ------------------------------------------------------------------
    # Message splitting & pruning
    # ------------------------------------------------------------------

    def _split_messages(
        self, messages: list[BaseMessage]
    ) -> tuple[list[BaseMessage], list[BaseMessage]]:
        """Split into (recent_to_keep_verbatim, older_to_prune)."""
        if len(messages) <= self.recent_to_keep:
            return messages, []
        return messages[-self.recent_to_keep:], messages[:-self.recent_to_keep]

    def _prune_messages(
        self, messages: list[BaseMessage]
    ) -> tuple[str, list[dict]]:
        """
        Concatenate older messages into one text blob and run TF-IDF pruning.
        Returns (pruned_text, token_score_entries).
        """
        if not messages:
            return "", []
        concatenated = "\n".join(self._format_message(m) for m in messages)
        pruned, entries = self.pruner.score_and_prune(concatenated)
        return pruned, entries

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    def _fallback_sliding_window(
        self,
        constraint_prefix: str,
        messages: list[BaseMessage],
        user_query: str,
    ) -> str:
        """
        Emergency fallback: keep constraint prefix + as many recent messages
        as fit under a conservative token budget.
        """
        budget = self.pressure_threshold - estimate_tokens(constraint_prefix) - 100
        kept = []
        used = 0
        for msg in reversed(messages):
            formatted = self._format_message(msg)
            t = estimate_tokens(formatted)
            if used + t > budget:
                break
            kept.insert(0, formatted)
            used += t

        lines = []
        if constraint_prefix:
            lines.append(constraint_prefix)
            lines.append("")
        lines.extend(kept)
        lines.append(f"User: {user_query}")
        return "\n".join(lines)
