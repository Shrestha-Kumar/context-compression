# Context Compression Module — Friend Handoff Guide

## EVALUATION STRATEGY (Read This First)

Before touching any code, understand exactly how the evaluation works:

### The Core Idea
The evaluation proves that a Baseline agent (no compression) **forgets** critical user constraints when the conversation grows long, while the Compressed agent **retains** them.

### How a Single Test Runs
```
Turn 1:  User says "I'm allergic to shellfish, budget $3000"
         → This is the CRITICAL CONSTRAINT to remember

Turn 2-9: Noisy research turns (flights, hotels, weather)
           → Each padded with fake tool output (~500 tokens of noise)
           → This bloats the context past the model's "Lost in Middle" zone

Turn 10 (Final):  "Find me the best dinner spots. What should I be careful about?"
           → BASELINE:   Raw 4000-token context goes straight to Qwen → likely forgets shellfish
           → COMPRESSED: Pipeline extracts memory → only 200-token JSON state + recent turns go to Qwen
                         → Model sees "allergic to shellfish" in the memory header → PASS
```

### The Two Pipelines Being Compared
| | Baseline | Compressed |
|---|---|---|
| Context sent to LLM | Full raw history (3000-5000 tokens) | Memory JSON + recent 4 turns (~200-400 tokens) |
| Tier 1 | None | LLM CoT extraction → updates `MemoryState` JSON |
| Tier 2 | None | TF-IDF pruner drops low-relevance old turns |
| Result | Forgets early constraints | Retains all critical constraints |

### The 8 Test Scenarios
| Test | Tests For |
|---|---|
| A — The Forgotten Allergy | Medical constraint retention across 10 noisy turns |
| B — The Budget Anchor | Numerical state tracking + subtraction math |
| C — The Pivot | Stale context invalidation (Bali → Switzerland) |
| D — The Logistics Puzzle | Temporal cross-referencing with hard deadlines |
| E — The Contradiction Detector | Proactive boundary enforcement (max 2 activities) |
| F — The Distractor | Hallucination resistance to conflicting tool outputs |
| G — Session Resumption | Long-term memory anchor across simulated disconnect |
| H — The Budget Reversal | Refund/reversal math tracked through the changelog |

### The Two Evaluation Scripts
- **`evaluate_scenarios.py`** → Runs all 8 tests with A/B comparison table (BASELINE vs COMPRESSED)
- **`generate_context_filler.py`** → Runs one heavy scenario (120+ messages) and prints quantitative metrics (token count, compression ratio, latency, retained state)

---

## FILES I AM SENDING YOU

Copy these files into your cloned repo **replacing** any existing versions:

```
backend/agent/inference.py      <- Cleaned GPU-only pipeline, no mock/API code
backend/agent/graph.py          <- Added evaluate_baseline flag support
backend/agent/state.py          <- Added evaluate_baseline field to AgentState
backend/compression/pipeline.py <- Fixed system prompt schema for LLM extraction
evaluate_scenarios.py           <- 8-scenario A/B with realistic dialogue (NEW)
generate_context_filler.py      <- Synthetic context load test (NEW)
full_evaluation.py              <- All 13 quantitative metrics report (NEW)
plot_trajectory.py              <- 40-turn degradation graphs, saves compression_trajectory.png (NEW)
requirements.txt                <- Added matplotlib + duckduckgo_search
handoff_guide.md                <- This guide (NEW)
```

**Do NOT copy these — they are personal/local only:**
```
.env                            ← Contains my personal API key, irrelevant for GPU setup
requirements.txt                ← May have changes for my Python 3.13 — use your original
```

---

## SETUP GUIDE (For GPU Machine)

### Prerequisites
- CUDA-enabled GPU (your RTX setup)
- Python 3.10 (from your existing setup)
- The checkpoint file already in `training/checkpoints/qwen-constraint-tracker/checkpoint-63/`

### Step 1 — Install dependencies
```bash
micromamba activate dl
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### Step 2 — Verify GPU is detected
```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```
Expected output: `CUDA: True NVIDIA RTX ...`

### Step 3 — Run the main application
Open two terminals:
```bash
# Terminal 1 — Backend
PYTHONPATH=. python backend/app.py

# Terminal 2 — Frontend  
cd frontend && npm run dev
```
Then open `http://localhost:3000`

---

## RUNNING THE EVALUATION

There are three scripts. Run them in this order:

### 1. Quantitative Metrics — The Main Script (Run This For Judges)
```bash
PYTHONPATH=. python full_evaluation.py
```
This prints a structured report covering **all 9 required metrics**:
- Token Reduction & Compression Ratio
- Latency Reduction (real timing)
- Cost Reduction (USD/1k conversations)
- Downstream Task Success Rate
- Factual Retention Rate
- Coherence Over Long Turns
- Tool-Call Correctness
- Multi-Session Continuity
- Omission + Distortion Rate

### 2. A/B Scenario Suite — Baseline vs Compressed Comparison
```bash
PYTHONPATH=. python evaluate_scenarios.py
```
Runs 8 stress-test scenarios and prints a side-by-side table showing which tests the
uncompressed Baseline fails, and which the Compressed agent passes.

### 3. Synthetic Context Load Test — Token Counting Demo
```bash
PYTHONPATH=. python generate_context_filler.py
```
Pumps 120+ messages of noisy tool output through the pipeline and prints raw vs
compressed token counts with the extracted memory state.

---

## WHAT YOUR QWEN MODEL ACTUALLY DOES (vs What My Setup Did)

In the evaluation on my laptop (no GPU), I used a Groq cloud API temporarily. **That code is now completely removed.**

On your machine:
- `InferenceEngine.load()` detects CUDA → loads `Qwen/Qwen2.5-1.5B-Instruct`  
- LoRA adapters are injected from `checkpoint-63`
- All LLM calls go to your local model — zero external API
- Token counts, KV-cache stats, and VRAM metrics are all real measurements

No `.env` file is needed. No API keys. Completely self-contained.

---

## IF SOMETHING BREAKS

| Error | Fix |
|---|---|
| `ModuleNotFoundError: duckduckgo_search` | `pip install duckduckgo_search` |
| `GraphRecursionError: Recursion limit of 25` | The model is trying to call tools. Add `DO NOT CALL TOOLS. ANSWER DIRECTLY.` to the final query in the failing test. |
| `JSON missing critical root structures` | The pipeline's LLM prompt schema is pre-fixed — should not happen. If it does, check `backend/compression/pipeline.py` line 55. |
| VRAM OOM | Set `use_int4=True` in `InferenceConfig` in `backend/agent/inference.py` line 43 |
