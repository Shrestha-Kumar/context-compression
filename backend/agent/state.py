"""
LangGraph state schema.

The state is a TypedDict passed between every node in the graph. Each node
reads from and writes to this state. LangGraph handles persistence and
checkpointing automatically — we just define the shape.

The design principle: the constraint dict is the source of truth for user
requirements. The messages list is transient conversation history subject
to compression. Telemetry fields are append-only for the frontend.
"""

from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


# -----------------------------------------------------------------------------
# Memory State tracking sub-schema (Phase 9 overhaul)
# -----------------------------------------------------------------------------
# This is the information the agent must NEVER forget. It handles CRU/D operations
# and long-term user preferences beyond simple string-matching.

class ActiveTrip(TypedDict, total=False):
    destinations: list[str]
    dates: dict
    bookings: list[dict]

class UserProfile(TypedDict, total=False):
    routines: list[str]
    preferences: list[str]

class ChangelogEntry(TypedDict):
    date: str
    action: str

class MemoryState(TypedDict, total=False):
    """
    Dynamic, open-ended context tracking tracking current trip goals,
    user preferences routines, and temporal changes.
    """
    active_trip: ActiveTrip
    user_profile: UserProfile
    changelog: list[ChangelogEntry]

def empty_memory() -> MemoryState:
    """Factory for a fresh empty memory dict."""
    return {
        "active_trip": {"destinations": [], "dates": {}, "bookings": []},
        "user_profile": {"routines": [], "preferences": []},
        "changelog": []
    }


# -----------------------------------------------------------------------------
# Compression telemetry
# -----------------------------------------------------------------------------
# Append-only log of compression events for the frontend debugger.

class CompressionEvent(TypedDict):
    turn_number: int
    raw_tokens: int
    compressed_tokens: int
    ratio: float
    tier_used: str             # "none" | "tier1_only" | "tier1_and_tier2" | "fallback"


# -----------------------------------------------------------------------------
# The root state
# -----------------------------------------------------------------------------

class AgentState(TypedDict):
    """
    Central state object for the entire LangGraph workflow.

    The `messages` field uses LangGraph's `add_messages` reducer, which
    appends new messages rather than overwriting the list. Every other field
    is overwritten on each node update.
    """
    # Conversation
    messages: Annotated[list[BaseMessage], add_messages]
    turn_number: int

    # The persistent memory state — replacing old ConstraintDict
    memory: MemoryState

    # Compression state
    compression_history: list[CompressionEvent]
    last_compressed_prompt: Optional[str]   # What actually went to the LLM
    last_token_scores: Optional[list[dict]] # For frontend heatmap

    # KV-Cache tracking (for the visualizer)
    kv_sink_tokens: list[str]
    kv_recent_tokens: list[str]
    kv_evicted_count: int

    # Agent control
    pending_tool_call: Optional[dict]       # If LLM wants to call a tool
    needs_compression: bool                 # Set by pressure check node


def initial_state() -> AgentState:
    """Factory for a fresh session state."""
    return AgentState(
        messages=[],
        turn_number=0,
        memory=empty_memory(),
        compression_history=[],
        last_compressed_prompt=None,
        last_token_scores=None,
        kv_sink_tokens=[],
        kv_recent_tokens=[],
        kv_evicted_count=0,
        pending_tool_call=None,
        needs_compression=False,
    )
