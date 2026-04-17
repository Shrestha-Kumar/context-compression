"""
CPU-only compression demo.

Shows the two-tier compression pipeline working on a realistic 30-turn
travel conversation — no GPU, no model, just the compression logic.

Useful for:
  - Sanity-checking the pipeline before firing up expensive inference
  - Showing judges the compression numbers even if the model crashes
  - Debugging the constraint extractor and TF-IDF pruner

Usage:
    python run_demo.py
"""

from langchain_core.messages import HumanMessage, AIMessage

from backend.agent.state import empty_constraints
from backend.compression.pipeline import CompressionPipeline
from backend.compression.constraint_extractor import format_constraints_as_prompt


# A scripted 30-turn conversation — same as the benchmark
SCRIPTED = [
    "I want to plan a 2-week trip from Delhi to Paris, then Rome, with a budget around $3000.",
    "Important: my passport expires in exactly 14 days, so I can only visit countries with visa on arrival.",
    "What flights are available from Delhi to Paris on May 1st?",
    "Can you find some 4-star hotels in Paris for 3 nights?",
    "Also, I'm strictly vegan, so please keep that in mind for all dining.",
    "We're 2 adults traveling, no kids.",
    "Find me hotels in Rome for May 5-9.",
    "What about flights from Paris to Rome on May 5?",
    "Are there any good vegan restaurants in Rome?",
    "I'd prefer hotels with WiFi and breakfast included.",
    "Actually, let's change Paris to Lyon instead.",
    "Find flights from Delhi to Lyon on May 1.",
    "And hotels in Lyon for 3 nights.",
    "What vegan restaurants are in Lyon?",
    "Can you recheck the Rome hotel availability?",
    "I forgot to mention - I prefer budget options, nothing over $200/night for hotels.",
    "How much have we spent so far on hotels and flights?",
    "Let's swap Rome for Milan instead.",
    "Find flights from Lyon to Milan.",
    "Vegan restaurants in Milan?",
    "What's the weather like in Milan in May?",
    "Find 3-star hotels in Milan.",
    "Can I extend my Milan stay to 5 nights?",
    "Are there any museum discounts for tourists?",
    "What are some day-trip options from Milan?",
    "How do I get from the Milan airport to the city center?",
    "What's the tipping culture in Italy?",
    "I'm now considering adding a layover in Japan on the way. Japan requires 6 months passport validity. Can we do it?",
    "Okay, please summarize my full itinerary with all bookings.",
    "What's my total estimated cost?",
]


def run():
    pipeline = CompressionPipeline(
        pressure_threshold_tokens=1200,
        recent_messages_to_keep=4,
        target_ratio=0.55,
    )

    messages = []
    constraints = empty_constraints()

    print("=" * 70)
    print("CPU-ONLY COMPRESSION DEMO — 30-turn travel conversation")
    print("=" * 70)

    for turn_idx, user_text in enumerate(SCRIPTED, start=1):
        # Simulate: user speaks, then a stub assistant response gets appended.
        # The pipeline compresses the history EXCLUDING the new user message.
        result = pipeline.compress(
            messages=messages,
            current_constraints=constraints,
            user_query=user_text,
        )
        constraints = result.updated_constraints

        # After compression, append the user message + a stub assistant reply
        # to simulate conversation growth.
        messages.append(HumanMessage(content=user_text))
        # Make the stub assistant response verbose so context grows
        messages.append(AIMessage(
            content=f"Turn {turn_idx}: Here is a detailed response with some options and information "
                    f"that would typically come from the model. This is filler to simulate realistic "
                    f"response length for the compression demonstration."
        ))

        marker = ""
        if turn_idx == 2:
            marker = "  <-- NEEDLE INJECTED"
        if turn_idx == 28:
            marker = "  <-- NEEDLE PROBE"

        print(f"Turn {turn_idx:2d} | raw={result.raw_tokens:4d} "
              f"| compressed={result.compressed_tokens:4d} "
              f"| ratio={result.ratio:5.1%} "
              f"| tier={result.tier_used}{marker}")

    print()
    print("=" * 70)
    print("FINAL CONSTRAINT DICTIONARY (the 'secret weapon')")
    print("=" * 70)
    for k, v in constraints.items():
        if v:  # Skip empty fields
            print(f"  {k}: {v}")

    print()
    print("=" * 70)
    print("CONSTRAINT-PREFIX SYSTEM PROMPT (injected on every turn)")
    print("=" * 70)
    prefix = format_constraints_as_prompt(constraints)
    print(prefix)
    print(f"\nPrefix length: {len(prefix)} chars, ~{len(prefix) // 4} tokens")

    # Critical validation: the needle must survive
    print()
    print("=" * 70)
    print("NEEDLE SURVIVAL CHECK")
    print("=" * 70)
    passport = constraints.get("passport", {})
    if passport.get("expiry_days") == 14:
        print("  PASS  passport expiry (14 days) preserved in constraint dict")
    else:
        print(f"  FAIL  expected expiry_days=14, got {passport}")
    if passport.get("visa_restriction") == "visa_on_arrival_only":
        print("  PASS  visa_on_arrival restriction preserved")
    else:
        print(f"  FAIL  visa_restriction missing: {passport}")

    # Check city swaps
    cities = constraints.get("cities", [])
    if "Paris" not in cities and "Lyon" in cities:
        print("  PASS  Paris -> Lyon swap tracked correctly")
    else:
        print(f"  WARN  city list: {cities}")
    if "Rome" not in cities and "Milan" in cities:
        print("  PASS  Rome -> Milan swap tracked correctly")
    else:
        print(f"  WARN  city list: {cities}")


if __name__ == "__main__":
    run()
