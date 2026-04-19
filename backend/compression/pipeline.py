"""
Compression pipeline orchestrator.

Coordinates the two-tier compression strategy with a validation gate and
graceful fallback. The single entry point is `compress()`.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from backend.agent.state import MemoryState, empty_memory

logger = logging.getLogger(__name__)

@dataclass
class CompressionResult:
    compressed_prompt: str
    updated_constraints: MemoryState
    raw_tokens: int
    compressed_tokens: int
    ratio: float
    tier_used: str
    token_scores: List[Dict[str, Any]] = field(default_factory=list)

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)

def format_memory_as_prompt(memory: MemoryState) -> str:
    """Renders the memory dictionary as a system context prompt."""
    if not memory:
        return ""
    return f"[PERSISTENT MEMORY STATE (DO NOT FORGET)]\n{json.dumps(memory, indent=2)}\n"

class CompressionPipeline:
    def __init__(self, inference_engine=None, pressure_threshold_tokens: int = 1536, recent_messages_to_keep: int = 4):
        self.inference = inference_engine
        self.pressure_threshold = pressure_threshold_tokens
        self.recent_to_keep = recent_messages_to_keep

    def compress(self, messages: list[BaseMessage], current_constraints: MemoryState, user_query: str) -> CompressionResult:
        hist_lines = []
        for m in messages:
            role = {HumanMessage: "User", AIMessage: "Assistant", SystemMessage: "System", ToolMessage: "Tool"}.get(type(m), "Message")
            content = m.content if isinstance(m.content, str) else str(m.content)
            hist_lines.append(f"{role}: {content}")
        hist_lines.append(f"User: {user_query}")
        hist_str = "\n".join(hist_lines)
        
        system_prompt = "You are an intelligent Memory State Tracker. Given a conversation, evaluate changes to the persistent states step-by-step using a <thought> block. Then, extract the final state (active trips, routines, preferences) and record all additions, updates, and deletions into the changelog array. Always output the valid JSON object directly after the <thought> block."
        
        updated_memory = current_constraints
        tier_used = "llm_cot"
        
        # Hackathon deterministic heuristic: If the user just says "hello" or short phrases,
        # circumvent the LLM extraction because the LoRA weights overfit to the explicit travel dataset, 
        # causing false-positive hallucinations on empty context.
        if len(hist_str) < 30 and len(messages) <= 2:
            return CompressionResult(
                compressed_prompt="", 
                updated_constraints=current_constraints,
                raw_tokens=0,
                compressed_tokens=0,
                ratio=0.0,
                tier_used="heuristic_bypass"
            )
            
        if self.inference:
            try:
                # 1. TIER 1: LLM Chain-Of-Thought Extraction
                res = self.inference.generate(prompt=f"Extract the travel constraints from this conversation:\n\n{hist_str}", system_prompt=system_prompt)
                json_text = res.text.split("</thought>")[-1]
                start_idx = json_text.find("{")
                end_idx = json_text.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    json_str = json_text[start_idx:end_idx+1]
                else:
                    json_str = json_text.strip()
                    
                # Clean hallucinated unquoted dates (e.g. 2026-06-02 -> "2026-06-02")
                json_str = re.sub(r'(?<![a-zA-Z0-9_"-])(\d{4}-\d{2}-\d{2})(?![a-zA-Z0-9_"-])', r'"\1"', json_str)
                    
                extracted = json.loads(json_str)
                
                # Fix: LLM training data had hardcoded dates, meaning LoRA tensors memorized them causing static hallucination.
                # Overriding timeline logs explicitly with real-world time-series.
                import datetime
                real_date = datetime.datetime.now().strftime("%Y-%m-%d")
                if "changelog" in extracted:
                    for log in extracted["changelog"]:
                        log["date"] = real_date
                        
                if "active_trip" in extracted:
                    updated_memory = extracted
                    # Sanity filter: reject changelog entries that look like raw questions
                    # (longer than 120 chars or end with a '?') — these are LoRA hallucinations
                    # where the user's query text itself leaked into the extracted log.
                    if "changelog" in updated_memory:
                        updated_memory["changelog"] = [
                            e for e in updated_memory["changelog"]
                            if isinstance(e.get("action", ""), str)
                            and len(e["action"]) < 120
                            and not e["action"].strip().endswith("?")
                        ]
                else:
                    raise ValueError("JSON missing critical root structures.")
            except Exception as e:
                logger.warning(f"LLM Extraction failed ({e}). Returning fallback previous constraints.")
                tier_used = "llm_cot_failed"
                # Removed 'raise e' to prevent crash. Reverting to current memory loop safely!
                return CompressionResult(compressed_prompt="", updated_constraints=current_constraints, raw_tokens=0, compressed_tokens=0, ratio=0.0, tier_used=tier_used)
        
        # 3. TIER 2: String Formatting / Dropping Old Context
        memory_prefix = format_memory_as_prompt(updated_memory)
        raw_prompt = "\n".join(hist_lines)
        raw_tokens = estimate_tokens(raw_prompt)

        if raw_tokens <= self.pressure_threshold:
            prompt = memory_prefix + "\n" + raw_prompt
            tokens = estimate_tokens(prompt)
            return CompressionResult(
                compressed_prompt=prompt,
                updated_constraints=updated_memory,
                raw_tokens=raw_tokens,
                compressed_tokens=tokens,
                ratio=max(0.0, 1.0 - (tokens / max(1, raw_tokens))),
                tier_used="none",
            )

        # Fallback to pure recent truncation because TF-IDF uses ConstraintDict natively, breaking the MemoryState!
        recent = messages[-self.recent_to_keep:] if len(messages) > self.recent_to_keep else messages

        lines = [memory_prefix, "\n[RECENT TURNS]"]
        for m in recent:
            role = {HumanMessage: "User", AIMessage: "Assistant", SystemMessage: "System", ToolMessage: "Tool"}.get(type(m), "Message")
            content = m.content if isinstance(m.content, str) else str(m.content)
            lines.append(f"{role}: {content}")
        lines.append(f"User: {user_query}")
        
        compressed_prompt = "\n".join(lines)
        tokens = estimate_tokens(compressed_prompt)

        return CompressionResult(
            compressed_prompt=compressed_prompt,
            updated_constraints=updated_memory,
            raw_tokens=raw_tokens,
            compressed_tokens=tokens,
            ratio=max(0.0, 1.0 - (tokens / max(1, raw_tokens))),
            tier_used=tier_used,
        )
