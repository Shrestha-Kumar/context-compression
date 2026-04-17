# Context Compression Module — Hack 60

Problem Statement 3: Context Compression for AI Agents (HCLTech ETO × IIT Mandi, April 2026).

A two-tier compression system for a multi-city travel planning agent, designed to run an open-source SLM (Qwen2.5-1.5B) on constrained hardware (6–12 GB VRAM) while maintaining goal accuracy above 95% across 30-turn conversations.

---

## Architecture (One-Minute Tour)

**Tier 1 — Deterministic Constraint Extraction.** Regex + pattern matching on every message extracts structured constraints (budget, cities, dietary needs, passport rules) into a persistent dictionary. This dictionary is injected as a compact system-prompt prefix on every turn and is excluded from all compression. *This is what guarantees the needle test passes.*

**Tier 2 — TF-IDF Token Pruning.** For conversational history that does need compression, we score each token by self-information and prune the lowest-scoring tokens. Entities (proper nouns, numbers, dates, flight codes) are whitelisted and never pruned.

**Attention Sink KV-Cache.** PyTorch tensor slicing keeps the first 4 tokens permanently anchored in the KV-Cache alongside a rolling window of recent tokens. This stabilizes the attention matrix mathematically so the model stays coherent over sessions far longer than its native 2048-token context window.

**Quality Gate.** A validator checks that every critical entity from the constraint dictionary appears in the compressed prompt. If validation fails, the system falls back to simple sliding-window truncation rather than feeding corrupted context to the model.

---

## Project Structure

```
context-compression-module/
├── contracts/
│   └── ws_schema.py              # Shared WebSocket message types (source of truth)
├── backend/
│   ├── app.py                    # FastAPI server, WebSocket endpoint
│   ├── compression/
│   │   ├── constraint_extractor.py   # Tier 1: regex/pattern extraction
│   │   ├── tfidf_pruner.py           # Tier 2: TF-IDF token scoring
│   │   ├── kv_cache_sinks.py         # Attention Sink tensor slicing
│   │   ├── validator.py              # Quality gate
│   │   └── pipeline.py               # Orchestrator with fallback
│   ├── agent/
│   │   ├── state.py                  # LangGraph state schema
│   │   ├── tools.py                  # Mock flight/hotel/visa APIs
│   │   ├── inference.py              # Qwen2.5 loader + generation
│   │   └── graph.py                  # LangGraph StateGraph
│   └── evaluation/
│       ├── benchmark.py              # 30-turn scripted test with needle
│       └── metrics.py                # Comparison report generator
├── requirements.txt
└── README.md
```

---

## Setup

### Local (RTX 4050, 6 GB VRAM)

```bash
git clone <repo>
cd context-compression-module

python3.10 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Kaggle (P100 / T4, 16 GB VRAM)

In a Kaggle notebook, enable **GPU** accelerator, then:

```python
!pip install -q -r requirements.txt
```

---

## Running

### Local chat server

```bash
# From the project root
uvicorn backend.app:app --host 0.0.0.0 --port 8000

# Or directly:
python -m backend.app
```

WebSocket URL for the frontend: `ws://localhost:8000/ws`.

Health check: `http://localhost:8000/health`.

### Environment variables

| Variable   | Default | Purpose                                                 |
| ---------- | ------- | ------------------------------------------------------- |
| `USE_INT4` | `1`     | `0` disables INT4 quantization (for 16 GB+ GPUs)        |
| `PRELOAD`  | `0`     | `1` loads the model on server start instead of lazily   |

### Run the benchmark

```bash
python -m backend.evaluation.benchmark --mode both

# Then generate the comparison report:
python -m backend.evaluation.metrics --results-dir ./benchmark_results
```

Results land in `./benchmark_results/` as JSON + a `report.md`.

---

## WebSocket Contract

See `contracts/ws_schema.py` — the single source of truth that both the Python backend and the React frontend conform to.

**Frontend → Backend:**
- `{ "type": "user_message", "text": "..." }`
- `{ "type": "reset_session" }`

**Backend → Frontend (streamed during each turn):**
- `compression_stats` — raw vs compressed token counts
- `token_scores` — per-token TF-IDF scores for the heatmap
- `kv_cache_state` — sink tokens + recent tokens for the KV visualizer
- `constraint_update` — the live constraint dictionary
- `tool_call_status` — when a flight/hotel API is invoked
- `assistant_message` — the final response text for the turn

---

## Hardware Notes

On **RTX 4050 (6 GB)**:
- Model (INT4): ~1.1 GB
- KV-Cache (bounded by Attention Sink, window=1536): ~1.3 GB
- Activations + overhead: ~1.5 GB
- Total peak: ~4 GB, comfortably under 6 GB

On **Kaggle P100 (16 GB)**:
- Set `USE_INT4=0` and run in FP16 for faster inference during benchmarking.

---

## The Needle Test

Turn 2 injects: *"My passport expires in 14 days, so I can only visit countries with visa on arrival."*

Turn 28 probes: *"Japan requires 6 months passport validity. Can we add a layover there?"*

A correct compressed agent denies Japan, citing the 14-day expiry. The baseline agent (FIFO truncation) forgets by Turn 10 and confidently approves Japan — that's the failure mode our compression solves.

---

## License

MIT. Built for the Hack 60 Advanced AI & Robotics Hackathon.
