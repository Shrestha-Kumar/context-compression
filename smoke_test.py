"""
Smoke test for the compression pipeline.

Validates the pure-Python parts (no GPU/model needed):
  - Contract validation
  - Constraint extraction
  - TF-IDF pruning
  - Validator
  - Full pipeline orchestration with the needle scenario

Run from project root:
    python smoke_test.py
"""

import sys
import traceback
from typing import Callable

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


# -----------------------------------------------------------------------------
# Tiny test harness
# -----------------------------------------------------------------------------

_PASSES = 0
_FAILS = 0


def test(name: str):
    def decorator(fn: Callable):
        global _PASSES, _FAILS
        try:
            fn()
            print(f"  PASS  {name}")
            _PASSES += 1
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            _FAILS += 1
        except Exception as e:
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
            traceback.print_exc()
            _FAILS += 1
        return fn
    return decorator


# =============================================================================
# Contract tests
# =============================================================================

def test_contract():
    print("\n[contracts/ws_schema.py]")
    from contracts.ws_schema import is_valid_incoming, VALID_INCOMING_TYPES

    @test("valid user_message passes")
    def _():
        assert is_valid_incoming({"type": "user_message", "text": "hi"})

    @test("valid reset_session passes")
    def _():
        assert is_valid_incoming({"type": "reset_session"})

    @test("unknown type rejected")
    def _():
        assert not is_valid_incoming({"type": "hack"})

    @test("non-dict rejected")
    def _():
        assert not is_valid_incoming("not a dict")
        assert not is_valid_incoming(None)

    @test("expected outgoing types registered")
    def _():
        from contracts.ws_schema import VALID_OUTGOING_TYPES
        expected = {
            "assistant_message", "compression_stats", "token_scores",
            "kv_cache_state", "constraint_update", "tool_call_status", "error",
        }
        assert expected.issubset(VALID_OUTGOING_TYPES)


# =============================================================================
# Constraint extractor tests
# =============================================================================

def test_extractor():
    print("\n[backend/compression/constraint_extractor.py]")
    from backend.compression.constraint_extractor import (
        ConstraintExtractor, format_constraints_as_prompt,
    )
    from backend.agent.state import empty_constraints

    ex = ConstraintExtractor()

    @test("extracts USD budget from $3000")
    def _():
        result = ex.update(empty_constraints(), [
            HumanMessage(content="I want a trip with a budget of $3000"),
        ])
        assert result["budget"]["max_amount"] == 3000.0, result
        assert result["budget"]["currency"] == "USD"

    @test("extracts budget with comma separator")
    def _():
        result = ex.update(empty_constraints(), [
            HumanMessage(content="My budget is under $2,500 total"),
        ])
        assert result["budget"]["max_amount"] == 2500.0

    @test("extracts cities from known gazetteer")
    def _():
        result = ex.update(empty_constraints(), [
            HumanMessage(content="Plan a trip from Delhi to Paris, then Rome"),
        ])
        assert "Paris" in result["cities"]
        assert "Rome" in result["cities"]
        assert "Delhi" in result["cities"]

    @test("extracts passport expiry THE NEEDLE")
    def _():
        result = ex.update(empty_constraints(), [
            HumanMessage(content="my passport expires in 14 days"),
        ])
        assert result["passport"]["expiry_days"] == 14

    @test("extracts visa-on-arrival restriction")
    def _():
        result = ex.update(empty_constraints(), [
            HumanMessage(content="I can only visit countries with visa on arrival"),
        ])
        assert result["passport"]["visa_restriction"] == "visa_on_arrival_only"

    @test("extracts dietary keywords")
    def _():
        result = ex.update(empty_constraints(), [
            HumanMessage(content="I'm strictly vegan"),
        ])
        assert "vegan" in result["dietary"]

    @test("extracts multiple dietary over turns (merges)")
    def _():
        c1 = ex.update(empty_constraints(), [
            HumanMessage(content="I'm vegan"),
        ])
        c2 = ex.update(c1, [
            HumanMessage(content="I'm vegan"),  # repeat should not duplicate
            HumanMessage(content="also gluten-free please"),
        ])
        assert c2["dietary"].count("vegan") == 1
        assert "gluten-free" in c2["dietary"]

    @test("handles city change: Paris -> Lyon")
    def _():
        constraints = ex.update(empty_constraints(), [
            HumanMessage(content="Let's go to Paris and then Rome"),
        ])
        assert "Paris" in constraints["cities"]
        constraints = ex.update(constraints, [
            HumanMessage(content="Actually, let's change Paris to Lyon instead."),
        ])
        assert "Lyon" in constraints["cities"], constraints["cities"]
        assert "Paris" not in constraints["cities"], constraints["cities"]

    @test("extracts traveler count")
    def _():
        r = ex.update(empty_constraints(), [
            HumanMessage(content="We're 2 adults traveling with 1 child"),
        ])
        assert r["travelers"]["adults"] == 2
        assert r["travelers"]["children"] == 1

    @test("extracts hotel star preferences")
    def _():
        r = ex.update(empty_constraints(), [
            HumanMessage(content="I'd prefer a 4-star hotel"),
        ])
        assert r["hotel_preferences"]["min_stars"] == 4

    @test("format_constraints_as_prompt produces compact output")
    def _():
        c = {
            "budget": {"max_amount": 3000.0, "currency": "USD", "per_person": False},
            "cities": ["Lyon", "Rome"],
            "dietary": ["vegan"],
            "passport": {"expiry_days": 14, "visa_restriction": "visa_on_arrival_only"},
            "booked_flights": [],
            "booked_hotels": [],
        }
        prompt = format_constraints_as_prompt(c)
        assert "3000" in prompt
        assert "Lyon" in prompt
        assert "Rome" in prompt
        assert "vegan" in prompt
        assert "14" in prompt
        # Should be short - under ~400 chars for this many constraints
        assert len(prompt) < 500, f"prompt too long: {len(prompt)}"

    @test("format_constraints handles empty dict")
    def _():
        assert format_constraints_as_prompt(empty_constraints()) == ""

    @test("ignores nonsense budgets (under $100 or over $100k)")
    def _():
        r = ex.update(empty_constraints(), [
            HumanMessage(content="I bought it for $5 the other day"),
        ])
        assert "budget" not in r, r


# =============================================================================
# TF-IDF pruner tests
# =============================================================================

def test_pruner():
    print("\n[backend/compression/tfidf_pruner.py]")
    from backend.compression.tfidf_pruner import TFIDFPruner

    pruner = TFIDFPruner(target_ratio=0.5)

    @test("preserves capitalized proper nouns")
    def _():
        text = "I want to visit Paris and Rome in the summer"
        pruned, entries = pruner.score_and_prune(text)
        preserved = [e["text"] for e in entries if e["preserved"]]
        assert "Paris" in preserved, preserved
        assert "Rome" in preserved, preserved

    @test("preserves numbers and currency")
    def _():
        text = "Please find flights under $3000 with 2 stops"
        pruned, entries = pruner.score_and_prune(text)
        preserved = [e["text"] for e in entries if e["preserved"]]
        # TF-IDF tokenizer splits "$3000" as "$3000", just "3000" is acceptable
        found_money = any(
            "3000" in p or "$3000" in p for p in preserved
        )
        assert found_money, f"3000 not preserved: {preserved}"

    @test("preserves flight codes")
    def _():
        text = "I booked flight AF1234 yesterday"
        pruned, entries = pruner.score_and_prune(text)
        preserved = [e["text"] for e in entries if e["preserved"]]
        assert "AF1234" in preserved, preserved

    @test("prunes common stopwords")
    def _():
        text = "the the the the the cat sat on the mat"
        pruned, entries = pruner.score_and_prune(text)
        # "the" should be heavily pruned
        the_preserved = sum(
            1 for e in entries if e["text"].lower() == "the" and e["preserved"]
        )
        the_total = sum(1 for e in entries if e["text"].lower() == "the")
        assert the_preserved < the_total, f"no stopword pruning: {the_preserved}/{the_total}"

    @test("entities get score 1.0")
    def _():
        text = "Fly to Paris on $3000 budget"
        pruned, entries = pruner.score_and_prune(text)
        for e in entries:
            if e["is_entity"]:
                assert e["score"] == 1.0, f"entity score wrong: {e}"

    @test("handles empty input gracefully")
    def _():
        pruned, entries = pruner.score_and_prune("")
        assert pruned == ""
        assert entries == []

    @test("empty-after-pruning scenario")
    def _():
        # All stopwords, no entities
        text = "the and or but if so then"
        pruned, entries = pruner.score_and_prune(text)
        assert isinstance(pruned, str)  # should not crash


# =============================================================================
# Validator tests
# =============================================================================

def test_validator():
    print("\n[backend/compression/validator.py]")
    from backend.compression.validator import CompressionValidator

    v = CompressionValidator()

    @test("passes when all entities present")
    def _():
        result = v.validate(
            compressed_text="Budget 3000 USD, cities Paris and Rome, vegan dining",
            constraints={
                "budget": {"max_amount": 3000.0, "currency": "USD"},
                "cities": ["Paris", "Rome"],
                "dietary": ["vegan"],
                "booked_flights": [],
                "booked_hotels": [],
            },
        )
        assert result.passed, result.missing_entities

    @test("fails when a city is missing")
    def _():
        result = v.validate(
            compressed_text="Budget 3000, heading to Paris for vegan food",
            constraints={
                "cities": ["Paris", "Rome"],   # Rome missing from text
                "dietary": ["vegan"],
                "budget": {"max_amount": 3000.0, "currency": "USD"},
                "booked_flights": [],
                "booked_hotels": [],
            },
        )
        assert not result.passed
        assert any("Rome" in m for m in result.missing_entities)

    @test("fails when passport expiry missing")
    def _():
        result = v.validate(
            compressed_text="Paris, Rome, vegan, budget 3000",
            constraints={
                "passport": {"expiry_days": 14, "visa_restriction": "visa_on_arrival_only"},
                "cities": ["Paris", "Rome"],
                "dietary": ["vegan"],
                "budget": {"max_amount": 3000.0, "currency": "USD"},
                "booked_flights": [],
                "booked_hotels": [],
            },
        )
        assert not result.passed

    @test("accepts budget in comma format")
    def _():
        result = v.validate(
            compressed_text="Budget 3,000 USD total",
            constraints={
                "budget": {"max_amount": 3000.0, "currency": "USD"},
                "cities": [],
                "dietary": [],
                "booked_flights": [],
                "booked_hotels": [],
            },
        )
        assert result.passed, result.missing_entities


# =============================================================================
# Full pipeline integration test (the needle scenario)
# =============================================================================

def test_pipeline_needle():
    print("\n[backend/compression/pipeline.py  -- THE NEEDLE SCENARIO]")
    from backend.compression.pipeline import CompressionPipeline
    from backend.agent.state import empty_constraints

    pipe = CompressionPipeline(
        pressure_threshold_tokens=400,   # trigger compression aggressively
        recent_messages_to_keep=3,
        target_ratio=0.5,
    )

    # Build a realistic 30-turn history with the needle at Turn 2
    messages = [
        HumanMessage(content="Plan a trip from Delhi to Paris, then Rome, budget $3000"),
        AIMessage(content="Great, let me help plan that trip."),
        # THE NEEDLE
        HumanMessage(content="Important: my passport expires in exactly 14 days, so I can only visit countries with visa on arrival."),
        AIMessage(content="Noted, I'll only suggest visa-on-arrival destinations."),
    ]

    # Pad with lots of filler to force compression
    for i in range(3, 30):
        messages.append(HumanMessage(content=f"Turn {i}: can you find me some hotels with different amenities and preferences and options in the area I want to visit"))
        messages.append(AIMessage(content=f"Here are several hotel options for you with various amenities like wifi pool gym breakfast included and so on across multiple price points"))

    @test("pipeline runs end-to-end without crashing")
    def _():
        result = pipe.compress(
            messages=messages,
            current_constraints=empty_constraints(),
            user_query="Can we add a layover in Japan? Japan requires 6 months passport validity.",
        )
        assert result.compressed_prompt
        assert result.tier_used in {"tier1_only", "tier1_and_tier2", "fallback"}

    @test("constraint dict captures passport expiry from Turn 2")
    def _():
        result = pipe.compress(
            messages=messages,
            current_constraints=empty_constraints(),
            user_query="Probe",
        )
        assert "passport" in result.updated_constraints, result.updated_constraints
        assert result.updated_constraints["passport"]["expiry_days"] == 14

    @test("constraint dict captures visa restriction from Turn 2")
    def _():
        result = pipe.compress(
            messages=messages,
            current_constraints=empty_constraints(),
            user_query="Probe",
        )
        assert result.updated_constraints["passport"]["visa_restriction"] == "visa_on_arrival_only"

    @test("compressed prompt contains 14 (the needle) even under heavy compression")
    def _():
        result = pipe.compress(
            messages=messages,
            current_constraints=empty_constraints(),
            user_query="Probe",
        )
        # The needle MUST survive because it lives in the constraint prefix
        assert "14" in result.compressed_prompt, (
            f"NEEDLE LOST. Prompt length: {len(result.compressed_prompt)}. "
            f"tier={result.tier_used}"
        )

    @test("compressed prompt contains visa info")
    def _():
        result = pipe.compress(
            messages=messages,
            current_constraints=empty_constraints(),
            user_query="Probe",
        )
        assert "visa" in result.compressed_prompt.lower()

    @test("compression achieves meaningful ratio under pressure")
    def _():
        result = pipe.compress(
            messages=messages,
            current_constraints=empty_constraints(),
            user_query="Probe",
        )
        # With 60 messages and aggressive threshold, we should see real compression
        if result.tier_used == "tier1_and_tier2":
            assert result.ratio > 0.1, f"ratio too low: {result.ratio}"

    @test("validation attaches to result when Tier 2 runs")
    def _():
        result = pipe.compress(
            messages=messages,
            current_constraints=empty_constraints(),
            user_query="Probe",
        )
        if result.tier_used in {"tier1_and_tier2", "fallback"}:
            assert result.validation is not None


# =============================================================================
# KV-Cache slicer test (CPU tensors - no GPU needed)
# =============================================================================

def test_kv_cache():
    print("\n[backend/compression/kv_cache_sinks.py]")
    try:
        import torch
    except ImportError:
        print("  SKIP  torch not installed in this env")
        return

    from backend.compression.kv_cache_sinks import (
        apply_attention_sinks_to_kv_cache, cache_seq_len,
    )

    @test("no-op when None")
    def _():
        assert apply_attention_sinks_to_kv_cache(None, 100, 4) is None
        assert cache_seq_len(None) == 0

    @test("legacy tuple cache: preserves sinks + recent when sliced")
    def _():
        # Simulate a legacy [batch, heads, seq, head_dim] cache with 3 layers
        batch, heads, seq, dim = 1, 4, 100, 32
        cache = tuple(
            (
                torch.arange(batch * heads * seq * dim, dtype=torch.float32).reshape(batch, heads, seq, dim),
                torch.arange(batch * heads * seq * dim, dtype=torch.float32).reshape(batch, heads, seq, dim),
            )
            for _ in range(3)
        )
        pruned = apply_attention_sinks_to_kv_cache(cache, window_size=20, sink_size=4)
        # After slicing: 4 sink + 16 recent = 20 tokens
        assert pruned[0][0].shape[2] == 20
        # First 4 tokens preserved (sinks)
        assert torch.equal(pruned[0][0][:, :, :4, :], cache[0][0][:, :, :4, :])
        # Last 16 tokens preserved (recent)
        assert torch.equal(pruned[0][0][:, :, 4:, :], cache[0][0][:, :, -16:, :])

    @test("no-op when seq_len <= window")
    def _():
        batch, heads, seq, dim = 1, 4, 10, 32
        cache = (
            (torch.zeros(batch, heads, seq, dim), torch.zeros(batch, heads, seq, dim)),
        )
        pruned = apply_attention_sinks_to_kv_cache(cache, window_size=20, sink_size=4)
        assert pruned[0][0].shape[2] == 10

    @test("cache_seq_len reports correctly")
    def _():
        cache = (
            (torch.zeros(1, 4, 50, 32), torch.zeros(1, 4, 50, 32)),
        )
        assert cache_seq_len(cache) == 50


# =============================================================================
# Mock tools test
# =============================================================================

def test_tools():
    print("\n[backend/agent/tools.py]")
    from backend.agent.tools import flight_search, hotel_search, visa_requirements, TOOL_MAP
    import json

    @test("flight_search returns valid JSON")
    def _():
        r = flight_search.invoke({"origin": "Paris", "destination": "Rome", "date": "2026-05-01"})
        data = json.loads(r)
        assert "options" in data
        assert len(data["options"]) > 0
        assert "flight_code" in data["options"][0]

    @test("hotel_search returns valid JSON")
    def _():
        r = hotel_search.invoke({"city": "Paris", "check_in": "2026-05-01", "check_out": "2026-05-04", "min_stars": 3})
        data = json.loads(r)
        assert "options" in data
        assert all(o["stars"] >= 3 for o in data["options"])

    @test("visa_requirements returns Japan = 6 months")
    def _():
        r = visa_requirements.invoke({"country": "Japan"})
        data = json.loads(r)
        assert data["min_passport_validity_months"] == 6
        assert data["visa_on_arrival"] is False

    @test("visa_requirements returns Thailand = visa on arrival")
    def _():
        r = visa_requirements.invoke({"country": "Thailand"})
        data = json.loads(r)
        assert data["visa_on_arrival"] is True

    @test("TOOL_MAP registers all 4 tools")
    def _():
        assert len(TOOL_MAP) == 4
        for name in ["flight_search", "hotel_search", "restaurant_search", "visa_requirements"]:
            assert name in TOOL_MAP


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 60)
    print("Context Compression Module - Smoke Test")
    print("=" * 60)

    test_contract()
    test_extractor()
    test_pruner()
    test_validator()
    test_pipeline_needle()
    test_kv_cache()
    test_tools()

    print()
    print("=" * 60)
    print(f"Results: {_PASSES} passed, {_FAILS} failed")
    print("=" * 60)

    return 0 if _FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
