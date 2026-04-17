"""
30-turn scripted evaluation benchmark.

Runs a realistic multi-city travel planning conversation against both the
baseline (FIFO truncation) and compressed agent. Injects a "needle" constraint
at Turn 2 that the agent must recall at Turn 28.

Output: JSON files with per-turn metrics + final compliance score.

Usage:
    python -m backend.evaluation.benchmark --mode compressed
    python -m backend.evaluation.benchmark --mode baseline
    python -m backend.evaluation.benchmark --mode both
"""

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from backend.agent.state import initial_state
from backend.agent.inference import InferenceEngine, InferenceConfig
from backend.agent.graph import TravelAgentGraph
from backend.compression.pipeline import CompressionPipeline


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("benchmark")


# -----------------------------------------------------------------------------
# The scripted conversation (30 turns)
# -----------------------------------------------------------------------------
# Turn 2 carries the "needle" — the passport/visa constraint that must
# survive until Turn 28 where it is probed.

SCRIPTED_TURNS = [
    # Turn 1: Open-ended request
    "I want to plan a 2-week trip from Delhi to Paris, then Rome, with a budget around $3000.",
    # Turn 2: THE NEEDLE — passport/visa constraint
    "Important: my passport expires in exactly 14 days, so I can only visit countries with visa on arrival.",
    # Turn 3-5: Initial exploration
    "What flights are available from Delhi to Paris on May 1st?",
    "Can you find some 4-star hotels in Paris for 3 nights?",
    "Also, I'm strictly vegan, so please keep that in mind for all dining.",
    # Turn 6-10: Adding details
    "We're 2 adults traveling, no kids.",
    "Find me hotels in Rome for May 5-9.",
    "What about flights from Paris to Rome on May 5?",
    "Are there any good vegan restaurants in Rome?",
    "I'd prefer hotels with WiFi and breakfast included.",
    # Turn 11-15: Modifications and tool calls
    "Actually, let's change Paris to Lyon instead.",
    "Find flights from Delhi to Lyon on May 1.",
    "And hotels in Lyon for 3 nights.",
    "What vegan restaurants are in Lyon?",
    "Can you recheck the Rome hotel availability?",
    # Turn 16-20: More complexity
    "I forgot to mention — I prefer budget options, nothing over $200/night for hotels.",
    "How much have we spent so far on hotels and flights?",
    "Let's swap Rome for Milan instead.",
    "Find flights from Lyon to Milan.",
    "Vegan restaurants in Milan?",
    # Turn 21-25: Still more
    "What's the weather like in Milan in May?",
    "Find 3-star hotels in Milan.",
    "Can I extend my Milan stay to 5 nights?",
    "Are there any museum discounts for tourists?",
    "What are some day-trip options from Milan?",
    # Turn 26-27: Filler before the probe
    "How do I get from the Milan airport to the city center?",
    "What's the tipping culture in Italy?",
    # Turn 28: THE PROBE — must recall the passport constraint from Turn 2
    "I'm now considering adding a layover in Japan on the way. Japan requires 6 months passport validity. Can we do it?",
    # Turn 29-30: Closing
    "Okay, please summarize my full itinerary with all bookings.",
    "What's my total estimated cost?",
]


# -----------------------------------------------------------------------------
# Data classes for results
# -----------------------------------------------------------------------------

@dataclass
class TurnResult:
    turn_number: int
    user_input: str
    assistant_output: str
    raw_tokens: int
    compressed_tokens: int
    compression_ratio: float
    tier_used: str
    latency_seconds: float
    vram_mb: float


@dataclass
class BenchmarkResult:
    mode: str                    # "compressed" | "baseline"
    turns: list[TurnResult]
    needle_probe_turn: int
    needle_test_passed: bool
    needle_response: str
    total_time_seconds: float
    avg_compression_ratio: float
    max_vram_mb: float
    final_constraints: dict


# -----------------------------------------------------------------------------
# Needle-check logic
# -----------------------------------------------------------------------------

def check_needle_response(response: str) -> bool:
    """
    Did the agent correctly reject the Japan layover?

    Correct behavior: mention the 14-day expiry AND/OR deny the Japan layover
    because 14 days < 6 months required.

    Heuristic: look for denial keywords + passport mention, OR explicit "14 days".
    """
    lower = response.lower()
    has_denial = any(
        word in lower for word in
        ["cannot", "can't", "unable", "not possible", "won't", "wouldn't", "not recommended"]
    )
    mentions_passport = any(
        word in lower for word in ["passport", "expire", "expir", "valid", "14 days", "14-day"]
    )
    mentions_japan = "japan" in lower
    # A good response denies AND explains via passport
    return mentions_japan and has_denial and mentions_passport


# -----------------------------------------------------------------------------
# Runner
# -----------------------------------------------------------------------------

def run_benchmark(
    mode: str,
    model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
    use_int4: bool = True,
    output_dir: Path = Path("./benchmark_results"),
) -> BenchmarkResult:
    """
    Run one full benchmark pass.

    Args:
        mode: "compressed" uses the full pipeline; "baseline" uses FIFO truncation.
    """
    output_dir.mkdir(exist_ok=True)

    config = InferenceConfig(model_name=model_name, use_int4=use_int4)
    engine = InferenceEngine(config)
    engine.load()

    if mode == "compressed":
        pipeline = CompressionPipeline(
            pressure_threshold_tokens=1536,
            recent_messages_to_keep=4,
            target_ratio=0.60,
        )
    elif mode == "baseline":
        # Baseline: a "compression" pipeline that never actually compresses
        # beyond Tier 1 name extraction. We simulate FIFO truncation by
        # setting the pressure threshold very high so Tier 2 never triggers.
        pipeline = CompressionPipeline(
            pressure_threshold_tokens=999_999,
            recent_messages_to_keep=999,
            target_ratio=1.0,
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")

    graph = TravelAgentGraph(inference_engine=engine, pipeline=pipeline)
    state = initial_state()

    turn_results: list[TurnResult] = []
    total_start = time.time()
    needle_probe_turn = 28
    needle_response = ""

    for turn_idx, user_input in enumerate(SCRIPTED_TURNS, start=1):
        logger.info(f"--- Turn {turn_idx} ---")
        logger.info(f"User: {user_input[:80]}...")

        start = time.time()
        try:
            state = graph.invoke(state, user_input)
        except Exception as e:
            logger.exception(f"Turn {turn_idx} failed")
            state["messages"].append(f"[ERROR: {e}]")
        latency = time.time() - start

        # Extract the last assistant message
        last_assistant = ""
        for m in reversed(state["messages"]):
            if hasattr(m, "content") and m.__class__.__name__ == "AIMessage":
                if not m.content.startswith("[Calling"):
                    last_assistant = m.content
                    break

        # Extract the compression event for this turn
        history = state.get("compression_history", [])
        last_event = history[-1] if history else {}

        turn_results.append(TurnResult(
            turn_number=turn_idx,
            user_input=user_input,
            assistant_output=last_assistant,
            raw_tokens=last_event.get("raw_tokens", 0),
            compressed_tokens=last_event.get("compressed_tokens", 0),
            compression_ratio=last_event.get("ratio", 0.0),
            tier_used=last_event.get("tier_used", "none"),
            latency_seconds=round(latency, 2),
            vram_mb=round(engine.vram_allocated_mb(), 1),
        ))

        if turn_idx == needle_probe_turn:
            needle_response = last_assistant

        logger.info(
            f"Turn {turn_idx}: ratio={last_event.get('ratio', 0):.2f} "
            f"tier={last_event.get('tier_used', 'none')} "
            f"latency={latency:.1f}s"
        )

    total_time = time.time() - total_start
    ratios = [t.compression_ratio for t in turn_results if t.raw_tokens > 0]
    avg_ratio = sum(ratios) / max(1, len(ratios))
    max_vram = max((t.vram_mb for t in turn_results), default=0.0)

    result = BenchmarkResult(
        mode=mode,
        turns=turn_results,
        needle_probe_turn=needle_probe_turn,
        needle_test_passed=check_needle_response(needle_response),
        needle_response=needle_response,
        total_time_seconds=round(total_time, 1),
        avg_compression_ratio=round(avg_ratio, 3),
        max_vram_mb=round(max_vram, 1),
        final_constraints=state.get("constraints", {}),
    )

    # Save to JSON
    output_file = output_dir / f"{mode}_results.json"
    with open(output_file, "w") as f:
        json.dump(_to_dict(result), f, indent=2, default=str)
    logger.info(f"Saved results to {output_file}")

    return result


def _to_dict(result: BenchmarkResult) -> dict:
    return {
        "mode": result.mode,
        "turns": [asdict(t) for t in result.turns],
        "needle_probe_turn": result.needle_probe_turn,
        "needle_test_passed": result.needle_test_passed,
        "needle_response": result.needle_response,
        "total_time_seconds": result.total_time_seconds,
        "avg_compression_ratio": result.avg_compression_ratio,
        "max_vram_mb": result.max_vram_mb,
        "final_constraints": result.final_constraints,
    }


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run the 30-turn benchmark")
    parser.add_argument("--mode", choices=["compressed", "baseline", "both"], default="both")
    parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--no-int4", action="store_true", help="Use FP16 instead of INT4")
    parser.add_argument("--output-dir", default="./benchmark_results")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    use_int4 = not args.no_int4

    if args.mode in ("compressed", "both"):
        logger.info("============ COMPRESSED AGENT ============")
        run_benchmark("compressed", args.model, use_int4, output_dir)

    if args.mode in ("baseline", "both"):
        logger.info("============ BASELINE AGENT ============")
        run_benchmark("baseline", args.model, use_int4, output_dir)


if __name__ == "__main__":
    main()
