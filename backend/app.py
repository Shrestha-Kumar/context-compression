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

from pydantic import BaseModel

class SummaryRequest(BaseModel):
    user_profile: dict
    changelog: list

@app.post("/generate_summary")
async def generate_summary(req: SummaryRequest):
    """
    Hackathon Requirement: "give a summary of choices and preferences... in a normal language"
    Abstracts the memory dictionary into a beautifully formatted readable document.
    """
    summary_text = "# User Travel Profile Summary\n\n"
    
    if req.user_profile.get("routines"):
        summary_text += "## General Routines\n"
        for r in req.user_profile["routines"]:
            summary_text += f"• {r}\n"
            
    if req.user_profile.get("preferences"):
        summary_text += "\n## Explicit Preferences\n"
        for p in req.user_profile["preferences"]:
            summary_text += f"• Likes {p}\n"
            
    if req.changelog:
        summary_text += "\n## System Audit Log (Temporal Tracking)\n"
        from collections import defaultdict
        from datetime import datetime
        grouped = defaultdict(list)
        for log in req.changelog:
            date_str = log.get('date', 'Unknown Date')
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                friendly_date = dt.strftime("%B %d")
            except ValueError:
                friendly_date = date_str
            grouped[friendly_date].append(log.get('action', ''))
            
        for d, actions in grouped.items():
            summary_text += f"\n## Date {d}\n"
            for a in actions:
                a_lower = a.lower()
                prefix = "Update"
                if "delete" in a_lower or "remove" in a_lower or "cancel" in a_lower:
                    prefix = "Delete"
                elif "add" in a_lower or "book" in a_lower:
                    prefix = "Add"
                    
                parts = a.split(":", 1)
                val = parts[1].strip() if len(parts) == 2 else a
                summary_text += f"# {prefix} : {val}\n"
            summary_text += "\n"
            
    if not req.user_profile.get("routines") and not req.user_profile.get("preferences"):
        summary_text += "No routines or preferences have been learned yet."
        
    return {"summary": summary_text}


# -----------------------------------------------------------------------------
# WebSocket endpoint
# -----------------------------------------------------------------------------

@app.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"WebSocket connected from {websocket.client}")

    graph = get_graph()
    state = initial_state()
    loop = asyncio.get_running_loop()

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

            if msg["type"] == "reset_session":
                state = initial_state()
                await websocket.send_json({
                    "type": "assistant_message",
                    "text": "[Session reset]",
                    "turn_number": 0,
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
