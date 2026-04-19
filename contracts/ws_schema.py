"""
WebSocket message schema — the single contract between backend and frontend.

This file is the authoritative source for every message type that flows over
the WebSocket connection. BOTH Claude (backend) and Antigravity (frontend)
must conform to these types.

Do not modify fields without updating both sides.
"""

from typing import Literal, TypedDict, Optional


# =============================================================================
# Frontend  →  Backend
# =============================================================================

class UserMessage(TypedDict):
    """User types a new message into the chat."""
    type: Literal["user_message"]
    text: str


class ResetSession(TypedDict):
    """User clicks the reset button; start a fresh conversation thread."""
    type: Literal["reset_session"]


# =============================================================================
# Backend  →  Frontend
# =============================================================================

class AssistantMessage(TypedDict):
    """Final assistant response to display in the chat."""
    type: Literal["assistant_message"]
    text: str
    turn_number: int


class CompressionStats(TypedDict):
    """High-level compression telemetry for the metrics chart."""
    type: Literal["compression_stats"]
    turn_number: int
    raw_tokens: int            # What the prompt would be without compression
    compressed_tokens: int     # What it actually is after compression
    ratio: float               # 1 - (compressed / raw); 0.0 to 1.0
    tier_used: Literal["none", "tier1_only", "tier1_and_tier2", "fallback"]
    vram_mb: float             # Current PyTorch CUDA memory allocation


class TokenScoreEntry(TypedDict):
    text: str                  # The token text
    score: float               # TF-IDF importance score, 0.0 to 1.0 (normalized)
    preserved: bool            # Did this token survive the pruning pass?
    is_entity: bool            # Was it whitelisted (proper noun, number, date)?


class TokenScores(TypedDict):
    """Per-token importance data for the heatmap visualization."""
    type: Literal["token_scores"]
    turn_number: int
    tokens: list[TokenScoreEntry]
    threshold: float           # Pruning threshold that was applied


class KVCacheState(TypedDict):
    """Snapshot of the KV-Cache sliding window for the visualizer."""
    type: Literal["kv_cache_state"]
    turn_number: int
    sink_tokens: list[str]     # Permanently-anchored initial tokens (typically 4)
    recent_tokens: list[str]   # Most recent tokens in the window
    evicted_count: int         # How many tokens have been evicted total
    window_size: int           # Max window size in the KV cache


class ConstraintUpdate(TypedDict):
    """The live constraint dictionary snapshot for the sidebar."""
    type: Literal["constraint_update"]
    turn_number: int
    constraints: dict          # The full constraint dict — see state.py


class ToolCallStatus(TypedDict):
    """Signals that the agent is calling an external tool."""
    type: Literal["tool_call_status"]
    tool_name: str             # e.g. "flight_search"
    status: Literal["running", "complete", "error"]
    result_summary: Optional[str]   # One-line summary when complete


class ErrorEvent(TypedDict):
    """Backend encountered an error; surface it to the UI."""
    type: Literal["error"]
    message: str
    fatal: bool


# =============================================================================
# Validation helpers
# =============================================================================

VALID_INCOMING_TYPES = {"user_message", "reset_session", "identify"}

VALID_OUTGOING_TYPES = {
    "assistant_message",
    "compression_stats",
    "token_scores",
    "kv_cache_state",
    "constraint_update",
    "tool_call_status",
    "error",
}


def is_valid_incoming(msg: dict) -> bool:
    """Quick check at the WebSocket boundary — reject malformed frontend input."""
    return isinstance(msg, dict) and msg.get("type") in VALID_INCOMING_TYPES
