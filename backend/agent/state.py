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
# Constraint dictionary sub-schema
# -----------------------------------------------------------------------------
# This is the information the agent must NEVER forget. It gets injected as a
# compact system prompt prefix on every turn and is excluded from compression.

class BudgetConstraint(TypedDict, total=False):
    max_amount: float
    currency: str
    per_person: bool


class PassportConstraint(TypedDict, total=False):
    expiry_days: int
    visa_restriction: str      # e.g. "visa_on_arrival_only"


class ConstraintDict(TypedDict, total=False):
    """
    The persistent constraint dictionary. Every field is optional because
    users reveal constraints progressively across turns.
    """
    budget: BudgetConstraint
    cities: list[str]          # Ordered list of cities in the itinerary
    origin: Optional[str]      # Starting city
    travel_dates: dict         # e.g. {"start": "2026-05-01", "end": "2026-05-14"}
    dietary: list[str]         # e.g. ["vegan", "halal"]
    passport: PassportConstraint
    travelers: dict            # e.g. {"adults": 2, "children": 1}
    hotel_preferences: dict    # e.g. {"min_stars": 4, "must_have": ["wifi"]}
    booked_flights: list[dict] # Confirmed flight selections
    booked_hotels: list[dict]  # Confirmed hotel selections


def empty_constraints() -> ConstraintDict:
    """Factory for a fresh empty constraint dict."""
    return {
        "cities": [],
        "dietary": [],
        "booked_flights": [],
        "booked_hotels": [],
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

    # The persistent constraint dictionary — our "secret weapon"
    constraints: ConstraintDict

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
        constraints=empty_constraints(),
        compression_history=[],
        last_compressed_prompt=None,
        last_token_scores=None,
        kv_sink_tokens=[],
        kv_recent_tokens=[],
        kv_evicted_count=0,
        pending_tool_call=None,
        needs_compression=False,
    )
