"""
FastAPI WebSocket server.

Entry point for the backend. Serves one endpoint:
    ws://localhost:8000/ws

Message flow:
    Frontend sends {type: "user_message", text: "..."}
    Backend:
        - Processes via LangGraph
        - Streams events: compression_stats, token_scores, kv_cache_state,
          constraint_update, tool_call_status, assistant_message
        - Final event is always an assistant_message (for that turn)

One WebSocket connection == one conversation thread. Reset the session by
sending {type: "reset_session"} or reconnecting.
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.agent.state import initial_state
from backend.agent.inference import InferenceEngine, InferenceConfig
from backend.agent.graph import TravelAgentGraph
from backend.compression.pipeline import CompressionPipeline
from contracts.ws_schema import is_valid_incoming
from backend.storage import storage
import uuid


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("app")


# -----------------------------------------------------------------------------
# Shared resources (one per process)
# -----------------------------------------------------------------------------

_ENGINE: InferenceEngine | None = None
_GRAPH: TravelAgentGraph | None = None


def get_graph() -> TravelAgentGraph:
    global _ENGINE, _GRAPH
    if _GRAPH is None:
        # Forcing INT4 loading to natively align with QLoRA trained checkpoints avoiding precision misalignment logic override.
        config = InferenceConfig(use_int4=True)
        _ENGINE = InferenceEngine(config)
        _GRAPH = TravelAgentGraph(
            inference_engine=_ENGINE,
            pipeline=CompressionPipeline(
                inference_engine=_ENGINE,
                pressure_threshold_tokens=1536,
                recent_messages_to_keep=4,
            ),
        )
        logger.info("Graph initialized (model loads lazily on first request)")
    return _GRAPH


# -----------------------------------------------------------------------------
# Lifecycle
# -----------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting context-compression-module server")
    # Pre-warm on startup in production; skip for dev hot-reload speed
    if os.getenv("PRELOAD", "0") == "1":
        logger.info("Pre-warming model...")
        get_graph()._ = None  # force initialization
        _ENGINE.load()
    yield
    logger.info("Shutting down")


app = FastAPI(title="Context Compression Module", lifespan=lifespan)

# CORS: allow the React frontend on localhost:3000 (default Next.js dev port)
# and also Antigravity's default ports.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)


# -----------------------------------------------------------------------------
# Health check
# -----------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"status": "ok", "service": "context-compression-module"}


@app.get("/health")
async def health():
    import torch
    return {
        "status": "ok",
        "cuda_available": torch.cuda.is_available(),
        "vram_allocated_mb": (
            torch.cuda.memory_allocated() / (1024 * 1024)
            if torch.cuda.is_available() else 0
        ),
    }

# -----------------------------------------------------------------------------
# Sessions API
# -----------------------------------------------------------------------------

@app.get("/sessions")
async def list_sessions():
    return {"sessions": storage.get_sessions()}

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    state = storage.get_session_state(session_id)
    if not state:
        return {"error": "Session not found"}, 404
    # Serializing BaseMessages for frontend if needed, though they are usually
    # handled via the JSON text in the DB.
    from langchain_core.messages import messages_to_dict
    return {
        "id": state["id"],
        "name": state["name"],
        "memory": state["memory"],
        "compression_history": state["compression_history"],
        "messages": messages_to_dict(state["messages"])
    }

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    storage.delete_session(session_id)
    return {"status": "deleted"}


from pydantic import BaseModel

class SummaryRequest(BaseModel):
    user_profile: dict = {}
    changelog: list = []
    active_trip: dict = {}
    memory: dict = {}   # Full MemoryState if available

@app.post("/generate_summary")
async def generate_summary(req: SummaryRequest):
    """
    Hackathon Requirement: Structured Markdown export of the full user memory state.
    Groups audit logs chronologically, renders trip details + preferences in plain language.
    """
    from collections import defaultdict
    from datetime import datetime

    # Support both old format {user_profile, changelog} and new full {memory}
    memory = req.memory if req.memory else {}
    user_profile = memory.get("user_profile") or req.user_profile or {}
    active_trip   = memory.get("active_trip")  or req.active_trip  or {}
    changelog     = memory.get("changelog")    or req.changelog    or []

    lines = ["# User Travel Profile Summary\n"]

    # ── Active Trip ──────────────────────────────────────────────────────────
    if active_trip and any(active_trip.values()):
        lines.append("## Active Trip\n")
        dates = active_trip.get("dates", {})
        dests = active_trip.get("destinations", [])
        bookings = active_trip.get("bookings", [])
        budget = active_trip.get("budget")

        if dests:
            lines.append(f"• **Destinations:** {', '.join(dests)}")
        if dates:
            start = dates.get("start") or dates.get("departure", "")
            end   = dates.get("end")   or dates.get("return", "")
            if start or end:
                lines.append(f"• **Dates:** {start} → {end}")
        if budget:
            lines.append(f"• **Budget cap:** ${budget}")
        if bookings:
            for b in bookings:
                code = b.get("code", "")
                btype = b.get("type", "booking")
                notes = b.get("notes", "")
                lines.append(f"• **{btype.capitalize()}:** {code} {('— ' + notes) if notes else ''}")
        lines.append("")

    # ── User Profile ─────────────────────────────────────────────────────────
    routines = user_profile.get("routines", [])
    prefs    = user_profile.get("preferences", [])

    if routines:
        lines.append("## General Routines\n")
        for r in routines:
            lines.append(f"• {r}")
        lines.append("")

    if prefs:
        lines.append("## Explicit Preferences\n")
        for p in prefs:
            lines.append(f"• {p}")
        lines.append("")

    if not routines and not prefs and not active_trip:
        lines.append("_No profile data has been learned yet._\n")

    # ── Audit Log ─────────────────────────────────────────────────────────────
    if changelog:
        lines.append("## System Audit Log (Temporal Tracking)\n")
        grouped: dict = defaultdict(list)
        for log in changelog:
            date_str = log.get("date", "Unknown Date")
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                friendly = dt.strftime("%B %d, %Y")
            except ValueError:
                friendly = date_str
            grouped[friendly].append(log.get("action", ""))

        for d, actions in grouped.items():
            lines.append(f"### {d}")
            for a in actions:
                a_lower = a.lower()
                if any(w in a_lower for w in ["delete", "remove", "cancel"]):
                    prefix = "🗑 Delete"
                elif any(w in a_lower for w in ["update", "change", "modify"]):
                    prefix = "✏️ Update"
                else:
                    prefix = "➕ Add"
                parts = a.split(":", 1)
                val = parts[1].strip() if len(parts) == 2 else a
                lines.append(f"- {prefix}: {val}")
            lines.append("")

    return {"summary": "\n".join(lines)}


# -----------------------------------------------------------------------------
# WebSocket endpoint
# -----------------------------------------------------------------------------

@app.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"WebSocket connected from {websocket.client}")

    graph = get_graph()
    
    # Check for session_id in query params or initial message
    # For now, we wait for the first message to possibly contain a session_id
    # or we generate one if missing.
    session_id = str(uuid.uuid4())
    state = initial_state()
    loop = asyncio.get_running_loop()

    # Inform the frontend of the initial session_id
    await websocket.send_json({
        "type": "session_update",
        "session_id": session_id
    })

    # Emitter: synchronous-from-graph, but schedules the async send on the loop.
    def emit(event: dict) -> None:
        try:
            payload = json.dumps(event)
        except (TypeError, ValueError) as e:
            logger.warning(f"Could not serialize event: {e}")
            return
        logger.info(f"Submitting {event['type']} to async event loop...")
        asyncio.run_coroutine_threadsafe(
            _safe_send(websocket, payload), loop
        )

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                    "fatal": False,
                })
                continue

            if not is_valid_incoming(msg):
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg.get('type')}",
                    "fatal": False,
                })
                continue

            # Handle session identity
            if msg.get("session_id"):
                provided_id = msg["session_id"]
                if provided_id != session_id:
                    existing = storage.get_session_state(provided_id)
                    if existing:
                        session_id = provided_id
                        state["messages"] = existing["messages"]
                        state["memory"] = existing["memory"]
                        state["compression_history"] = existing["compression_history"]
                        state["turn_number"] = len(state["messages"])
                        logger.info(f"Identified existing session: {session_id}")
                    else:
                        # If not found, we keep current session_id or set it to provided_id as new
                        session_id = provided_id
                        logger.info(f"Starting new session with ID: {session_id}")
            
            if msg["type"] == "identify":
                # Responding with session_update confirms acknowledgement
                await websocket.send_json({
                    "type": "session_update",
                    "session_id": session_id,
                    "turn_number": state.get("turn_number", 0)
                })
                continue

            if msg["type"] == "reset_session":
                session_id = str(uuid.uuid4())
                state = initial_state()
                await websocket.send_json({
                    "type": "assistant_message",
                    "text": "[Session reset]",
                    "turn_number": 0,
                    "session_id": session_id
                })
                continue

            if msg["type"] == "user_message":
                text = msg.get("text", "").strip()
                if not text:
                    continue

                # Run the graph in a thread pool — model inference is blocking.
                try:
                    state = await loop.run_in_executor(
                        None,
                        lambda: graph.invoke(state, text, emit),
                    )
                    # Persist state after turn
                    state_to_save = dict(state)
                    state_to_save["id"] = session_id
                    storage.save_session(session_id, state_to_save)
                    logger.info(f"Saved session {session_id} after Turn {state.get('turn_number')}")
                    
                    # Send updated session info
                    await websocket.send_json({
                        "type": "session_update",
                        "session_id": session_id,
                        "turn_number": state.get("turn_number", 0)
                    })
                except Exception as e:
                    logger.exception("Graph invocation failed")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Backend error: {e}",
                        "fatal": False,
                    })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception:
        logger.exception("Unexpected WebSocket error")


async def _safe_send(ws: WebSocket, payload: str):
    """Send a message, swallowing disconnection errors."""
    try:
        await ws.send_text(payload)
    except Exception as e:
        logger.debug(f"Send failed (client likely disconnected): {e}")


# -----------------------------------------------------------------------------
# Dev entry
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
