"""
LangGraph StateGraph definition.

This is the orchestration brain. It defines:
  - Every node (pressure check, compression, LLM, tool execution)
  - The conditional routing between them
  - How state flows through the graph

Graph structure:

    user_input → pressure_check ──┬── (low pressure)  ──→ llm_node
                                   └── (high pressure) ──→ compression_node → llm_node

    llm_node ──┬── (plain response) ──→ END (emit assistant_message)
               └── (tool call)       ──→ tool_node → llm_node

An emitter callback is passed in so graph nodes can push events to the
frontend via WebSocket as they execute, rather than only at the end.
"""

import json
import logging
from typing import Annotated, TypedDict, Callable, Optional

from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage,
)
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import StateGraph, END

from backend.agent.state import AgentState, MemoryState, empty_memory
from backend.agent.tools import TOOL_MAP
from backend.agent.inference import InferenceEngine
from backend.compression.pipeline import CompressionPipeline, format_memory_as_prompt


logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Emitter: how graph nodes push events to the frontend
# -----------------------------------------------------------------------------

# An "emitter" is just a callable: emit(event_dict). The FastAPI layer passes
# in a callback that serializes to JSON and sends over the WebSocket. During
# tests we use a list-based emitter that records events.

Emitter = Callable[[dict], None]


def noop_emitter(event: dict) -> None:
    pass


# -----------------------------------------------------------------------------
# System prompt template
# -----------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """You are a concise multi-city travel planning assistant.

You help users plan trips with budget, dietary, and documentation constraints. You call tools when you need external data (flights, hotels, restaurants, visa rules) and respect every user constraint.

CRITICAL RULES:
- If the user has a passport with limited validity, only recommend countries where they can legally enter.
- If the user specifies a budget, never suggest options that exceed it.
- If the user specifies dietary restrictions, only recommend compatible restaurants.
- Keep responses brief (2-4 sentences). Do not re-list all constraints back to the user.

TOOL CALLING:
To call a tool, emit exactly this format and nothing else:
<tool_call>{"name": "<tool_name>", "arguments": {<json_args>}}</tool_call>

Available tools:
- flight_search(origin, destination, date)
- hotel_search(city, check_in, check_out, min_stars)
- restaurant_search(city, cuisine, dietary)
- visa_requirements(country)

After a tool returns, give a natural-language response summarizing the result."""


# -----------------------------------------------------------------------------
# Graph builder
# -----------------------------------------------------------------------------

class TravelAgentGraph:
    """
    Builds and compiles the LangGraph StateGraph.

    One instance of this class per server process — the graph is stateless.
    Per-conversation state lives in the AgentState dicts that flow through it.
    """

    def __init__(
        self,
        inference_engine: InferenceEngine,
        pipeline: Optional[CompressionPipeline] = None,
    ):
        self.inference = inference_engine
        self.pipeline = pipeline or CompressionPipeline(inference_engine=inference_engine)
        self._graph = self._build_graph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def invoke(
        self,
        state: AgentState,
        user_input: str,
        emitter: Emitter = noop_emitter,
    ) -> AgentState:
        """
        Process one user turn. Returns the updated state.
        The emitter is called with frontend events during processing.
        """
        state["turn_number"] = state.get("turn_number", 0) + 1

        # Add the user message to history
        state["messages"] = list(state.get("messages", [])) + [
            HumanMessage(content=user_input)
        ]

        # Run the graph to completion natively via configuration tracking
        final_state = self._graph.invoke(state, config={"configurable": {"emitter": emitter}})
            
        return final_state

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self):
        graph = StateGraph(AgentState)

        graph.add_node("pressure_check", self._pressure_check_node)
        graph.add_node("compress", self._compress_node)
        graph.add_node("llm", self._llm_node)
        graph.add_node("tool", self._tool_node)

        graph.set_entry_point("pressure_check")

        graph.add_conditional_edges(
            "pressure_check",
            lambda s: "compress" if s.get("needs_compression") else "llm",
            {"compress": "compress", "llm": "llm"},
        )
        graph.add_edge("compress", "llm")

        graph.add_conditional_edges(
            "llm",
            lambda s: "tool" if s.get("pending_tool_call") else END,
            {"tool": "tool", END: END},
        )
        # Loop: after a tool runs, we need the model to interpret the result
        graph.add_edge("tool", "pressure_check")

        return graph.compile()

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    def _pressure_check_node(self, state: AgentState) -> dict:
        """
        Estimate token count; decide whether compression is needed.
        """
        messages = state.get("messages", [])
        # Use the model's actual tokenizer for accuracy
        joined = "\n".join(
            (m.content if isinstance(m.content, str) else str(m.content))
            for m in messages
        )
        # Always force compression evaluation to yield rich telemetry for the Dashboard
        needs = True
        
        logger.info(f"[pressure_check] tokens={self.inference.count_tokens(joined)} needs_compression={needs}")

        return {"needs_compression": needs}

    def _compress_node(self, state: AgentState, config: RunnableConfig) -> dict:
        """
        Run the two-tier compression pipeline. Updates constraints,
        generates the compressed prompt, emits telemetry.
        """
        def default_emitter(e: dict): pass
        emitter = config.get("configurable", {}).get("emitter", default_emitter)
        
        messages = state.get("messages", [])
        constraints = state.get("memory") or empty_memory()
        turn = state["turn_number"]

        # The user's latest message is the "query"
        last_human = next(
            (m for m in reversed(messages) if isinstance(m, HumanMessage)),
            None,
        )
        user_query = last_human.content if last_human else ""

        # Compress using all messages EXCEPT the final human one
        # (the final one is the current query, passed separately)
        history = [m for m in messages if m is not last_human]

        result = self.pipeline.compress(
            messages=history,
            current_constraints=constraints,
            user_query=user_query if isinstance(user_query, str) else str(user_query),
        )

        # Emit compression telemetry — skip on heuristic bypass to avoid wiping the metrics chart
        if result.tier_used != "heuristic_bypass" and result.raw_tokens > 0:
            emitter({
                "type": "compression_stats",
                "turn_number": turn,
                "raw_tokens": result.raw_tokens,
                "compressed_tokens": result.compressed_tokens,
                "ratio": round(result.ratio, 3),
                "tier_used": result.tier_used,
                "vram_mb": self.inference.vram_allocated_mb(),
            })

        if result.token_scores:
            emitter({
                "type": "token_scores",
                "turn_number": turn,
                "tokens": [
                    {
                        "text": e["text"],
                        "score": e["score"],
                        "preserved": e["preserved"],
                        "is_entity": e["is_entity"],
                    }
                    for e in result.token_scores[:300]  # UI cap
                ],
                "threshold": round(self.pipeline.pruner.target_ratio, 2),
            })

        emitter({
            "type": "constraint_update",
            "turn_number": turn,
            "constraints": result.updated_constraints,
        })

        # Record to compression history for benchmarks
        history_entry = {
            "turn_number": turn,
            "raw_tokens": result.raw_tokens,
            "compressed_tokens": result.compressed_tokens,
            "ratio": round(result.ratio, 3),
            "tier_used": result.tier_used,
        }

        # ---------------------------------------------------------------
        # Accumulate changelog across all turns so the MD export captures
        # every add/update/delete, not just the last LLM extraction.
        # ---------------------------------------------------------------
        new_memory = result.updated_constraints
        if isinstance(new_memory, dict):
            prev_changelog = constraints.get("changelog", []) if isinstance(constraints, dict) else []
            new_changelog = new_memory.get("changelog", [])
            # Merge: keep all historical entries, append any new ones not already present
            seen = {(e["date"], e["action"]) for e in prev_changelog}
            for entry in new_changelog:
                key = (entry.get("date", ""), entry.get("action", ""))
                if key not in seen:
                    prev_changelog.append(entry)
                    seen.add(key)
            new_memory["changelog"] = prev_changelog

        return {
            "memory": new_memory,
            "last_compressed_prompt": result.compressed_prompt,
            "last_token_scores": result.token_scores,
            "compression_history": state.get("compression_history", []) + [history_entry],
            "needs_compression": False,
        }

    def _llm_node(self, state: AgentState, config: RunnableConfig) -> dict:
        """
        Call the model. Construct prompt from either the compressed prompt
        (if we came through compress_node) or directly from messages.
        """
        def default_emitter(e: dict): pass
        emitter = config.get("configurable", {}).get("emitter", default_emitter)

        messages = state.get("messages", [])
        constraints = state.get("memory") or empty_memory()

        # Prefer the pre-compressed prompt if fresh
        compressed = state.get("last_compressed_prompt")
        
        # ALWAYS prepend the persistent memory state so the LLM NEVER forgets
        # hotel bookings, budgets, or routines even after KV-cache eviction truncates old turns.
        memory_prefix = format_memory_as_prompt(constraints)
        
        if compressed:
            # Injecting memory prefix even onto already-compressed prompts.
            prompt_text = (memory_prefix + "\n" + compressed) if memory_prefix else compressed
            clear_compressed = True
        else:
            # No compression needed this turn; build a simple prompt
            lines = []
            if memory_prefix:
                lines.append(memory_prefix)
                lines.append("")
            for m in messages:
                role = {
                    HumanMessage: "User",
                    AIMessage: "Assistant",
                    ToolMessage: "Tool",
                }.get(type(m), "Message")
                content = m.content if isinstance(m.content, str) else str(m.content)
                lines.append(f"{role}: {content}")
            prompt_text = "\n".join(lines)
            clear_compressed = False

        result = self.inference.generate(
            prompt=prompt_text,
            system_prompt=SYSTEM_PROMPT_TEMPLATE,
            use_lora=False
        )

        logger.info(f"Model Inference complete! Preparing to emit KV payload...")

        # Always emit the KV-cache state for visualization
        logger.info("Evaluating turn_number")
        tn = state["turn_number"]
        logger.info("Evaluating get_sink_tokens")
        st = self.inference.get_sink_tokens()
        logger.info("Evaluating evicted_count")
        ev = max(0, result.kv_seq_len_before - result.kv_seq_len_after)
        logger.info("Evaluating window_size")
        ws = self.inference.config.window_size
        
        logger.info("Calling emitter...")
        emitter({
             "type": "kv_cache_state",
             "turn_number": tn,
             "sink_tokens": st,
             "recent_tokens": [],
             "evicted_count": ev,
             "window_size": ws,
        })
        logger.info("Emitter finished successfully!")

        update: dict = {}

        if result.tool_call:
            # Model wants a tool call
            emitter({
                "type": "tool_call_status",
                "tool_name": result.tool_call["name"],
                "status": "running",
                "result_summary": None,
            })
            update["pending_tool_call"] = result.tool_call
            # DON'T add the raw tool-call text as a message; it clutters history.
            # We add a placeholder AI message indicating the tool call.
            update["messages"] = [
                AIMessage(content=f"[Calling {result.tool_call['name']}]")
            ]
        else:
            # Plain response — we're done for this turn
            emitter({
                "type": "assistant_message",
                "text": result.text,
                "turn_number": state["turn_number"],
            })
            update["messages"] = [AIMessage(content=result.text)]
            update["pending_tool_call"] = None

        if clear_compressed:
            update["last_compressed_prompt"] = None

        return update

    def _tool_node(self, state: AgentState, config: RunnableConfig) -> dict:
        """Execute a pending tool call and add the result to messages."""
        def default_emitter(e: dict): pass
        emitter = config.get("configurable", {}).get("emitter", default_emitter)
        tool_call = state.get("pending_tool_call")
        if not tool_call:
            return {}

        name = tool_call["name"]
        args = tool_call.get("arguments", {})

        tool = TOOL_MAP.get(name)
        if tool is None:
            result_text = json.dumps({"error": f"Unknown tool: {name}"})
            status = "error"
        else:
            try:
                result_text = tool.invoke(args)
                if not isinstance(result_text, str):
                    result_text = json.dumps(result_text)
                status = "complete"
            except Exception as e:
                logger.exception(f"Tool {name} failed")
                result_text = json.dumps({"error": str(e)})
                status = "error"

        emitter({
            "type": "tool_call_status",
            "tool_name": name,
            "status": status,
            "result_summary": self._summarize_tool_result(name, result_text),
        })

        return {
            "messages": [ToolMessage(content=result_text, tool_call_id=name)],
            "pending_tool_call": None,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _summarize_tool_result(self, tool_name: str, result_text: str) -> str:
        """One-liner summary of a tool result for the frontend status badge."""
        try:
            data = json.loads(result_text)
        except json.JSONDecodeError:
            return "(non-JSON result)"

        if "total_results" in data:
            return f"{data['total_results']} results"
        if "error" in data:
            return f"Error: {data['error']}"
        return "ok"
