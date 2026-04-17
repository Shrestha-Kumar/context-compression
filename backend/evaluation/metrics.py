"""
Metrics computation and report generation.

Loads benchmark result JSONs and produces a side-by-side comparison report.
Output: markdown + JSON suitable for the presentation.

Usage:
    python -m backend.evaluation.metrics --results-dir ./benchmark_results
"""

import argparse
import json
from pathlib import Path
from typing import Any


def load_results(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def summarize(run: dict) -> dict:
    turns = run["turns"]
    raw_totals = sum(t["raw_tokens"] for t in turns)
    compressed_totals = sum(t["compressed_tokens"] for t in turns)
    avg_latency = sum(t["latency_seconds"] for t in turns) / max(1, len(turns))
    max_raw = max((t["raw_tokens"] for t in turns), default=0)
    max_compressed = max((t["compressed_tokens"] for t in turns), default=0)

    return {
        "mode": run["mode"],
        "total_turns": len(turns),
        "total_raw_tokens": raw_totals,
        "total_compressed_tokens": compressed_totals,
        "aggregate_compression_ratio": (
            round(1 - compressed_totals / max(1, raw_totals), 3)
        ),
        "avg_per_turn_ratio": run["avg_compression_ratio"],
        "peak_raw_tokens": max_raw,
        "peak_compressed_tokens": max_compressed,
        "max_vram_mb": run["max_vram_mb"],
        "avg_latency_seconds": round(avg_latency, 2),
        "total_time_seconds": run["total_time_seconds"],
        "needle_test_passed": run["needle_test_passed"],
    }


def print_comparison(compressed: dict, baseline: dict):
    cs = summarize(compressed)
    bs = summarize(baseline)

    print()
    print("=" * 70)
    print("CONTEXT COMPRESSION MODULE — BENCHMARK COMPARISON")
    print("=" * 70)
    print()
    print(f"{'Metric':<35} {'Baseline':>15} {'Compressed':>15}")
    print("-" * 70)
    rows = [
        ("Total turns",                       bs["total_turns"],                  cs["total_turns"]),
        ("Total raw tokens",                  bs["total_raw_tokens"],             cs["total_raw_tokens"]),
        ("Total compressed tokens",           bs["total_compressed_tokens"],      cs["total_compressed_tokens"]),
        ("Aggregate compression ratio",       f"{bs['aggregate_compression_ratio']:.1%}", f"{cs['aggregate_compression_ratio']:.1%}"),
        ("Avg per-turn ratio",                f"{bs['avg_per_turn_ratio']:.1%}", f"{cs['avg_per_turn_ratio']:.1%}"),
        ("Peak raw tokens",                   bs["peak_raw_tokens"],              cs["peak_raw_tokens"]),
        ("Peak compressed tokens",            bs["peak_compressed_tokens"],       cs["peak_compressed_tokens"]),
        ("Max VRAM (MB)",                     bs["max_vram_mb"],                  cs["max_vram_mb"]),
        ("Avg latency per turn (s)",          bs["avg_latency_seconds"],          cs["avg_latency_seconds"]),
        ("Total wall-clock time (s)",         bs["total_time_seconds"],           cs["total_time_seconds"]),
    ]
    for label, b, c in rows:
        print(f"{label:<35} {str(b):>15} {str(c):>15}")
    print("-" * 70)
    print()
    print(f"NEEDLE TEST (Turn 28):")
    print(f"  Baseline:   {'PASS' if bs['needle_test_passed'] else 'FAIL'}")
    print(f"  Compressed: {'PASS' if cs['needle_test_passed'] else 'FAIL'}")
    print()

    # Needle response samples
    print("Baseline Turn-28 response:")
    print(f"  {baseline['needle_response'][:300]}")
    print()
    print("Compressed Turn-28 response:")
    print(f"  {compressed['needle_response'][:300]}")
    print()


def save_markdown_report(compressed: dict, baseline: dict, out_path: Path):
    cs = summarize(compressed)
    bs = summarize(baseline)
    lines = [
        "# Context Compression Module — Benchmark Report",
        "",
        "## Summary",
        "",
        "| Metric | Baseline | Compressed |",
        "| --- | ---: | ---: |",
        f"| Aggregate compression ratio | {bs['aggregate_compression_ratio']:.1%} | {cs['aggregate_compression_ratio']:.1%} |",
        f"| Avg per-turn ratio | {bs['avg_per_turn_ratio']:.1%} | {cs['avg_per_turn_ratio']:.1%} |",
        f"| Peak raw tokens | {bs['peak_raw_tokens']} | {cs['peak_raw_tokens']} |",
        f"| Peak compressed tokens | {bs['peak_compressed_tokens']} | {cs['peak_compressed_tokens']} |",
        f"| Max VRAM (MB) | {bs['max_vram_mb']} | {cs['max_vram_mb']} |",
        f"| Avg latency/turn (s) | {bs['avg_latency_seconds']} | {cs['avg_latency_seconds']} |",
        f"| Needle test | {'PASS' if bs['needle_test_passed'] else 'FAIL'} | {'PASS' if cs['needle_test_passed'] else 'FAIL'} |",
        "",
        "## Needle Test Responses (Turn 28)",
        "",
        "**Baseline:**",
        "",
        f"> {baseline['needle_response'][:500]}",
        "",
        "**Compressed:**",
        "",
        f"> {compressed['needle_response'][:500]}",
    ]
    out_path.write_text("\n".join(lines))
    print(f"Markdown report saved to {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="./benchmark_results")
    args = parser.parse_args()

    d = Path(args.results_dir)
    compressed_path = d / "compressed_results.json"
    baseline_path = d / "baseline_results.json"

    if not compressed_path.exists() or not baseline_path.exists():
        print(f"ERROR: missing {compressed_path} or {baseline_path}")
        print("Run the benchmark first: python -m backend.evaluation.benchmark --mode both")
        return

    compressed = load_results(compressed_path)
    baseline = load_results(baseline_path)

    print_comparison(compressed, baseline)
    save_markdown_report(compressed, baseline, d / "report.md")


if __name__ == "__main__":
    main()
