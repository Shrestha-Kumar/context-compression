"""
Synthetic Data Generator for Context Compression State Tracking.

This script generates training data by simulating multi-turn travel agent
conversations and producing the corresponding ConstraintDict JSON state.

You can use this in TWO ways:
  1. MANUAL MODE (default): Generates template conversations locally.
     No API key needed. Produces ~200 high-quality examples.
  2. API MODE: Uses Claude Sonnet / OpenAI GPT-4o-mini to generate
     diverse, natural conversations. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.

Usage:
    python generate_synthetic_data.py --mode manual --output train.jsonl
    python generate_synthetic_data.py --mode api --provider anthropic --num 500 --output train.jsonl
"""

import argparse
import json
import random
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# ConstraintDict schema reference (from backend/agent/state.py)
# ---------------------------------------------------------------------------
CONSTRAINT_SCHEMA = {
    "budget": {"max_amount": "float", "currency": "str", "per_person": "bool"},
    "cities": "list[str]",
    "origin": "str | null",
    "travel_dates": {"start": "str (YYYY-MM-DD)", "end": "str (YYYY-MM-DD)"},
    "dietary": "list[str] — values: vegan, vegetarian, halal, kosher, gluten-free, dairy-free, pescatarian",
    "passport": {"expiry_days": "int", "visa_restriction": "str"},
    "travelers": {"adults": "int", "children": "int"},
    "hotel_preferences": {"min_stars": "int", "must_have": "list[str]"},
    "booked_flights": [{"flight_code": "str", "price": "float"}],
    "booked_hotels": [{"name": "str", "stars": "int", "price_per_night": "float"}],
}

# ---------------------------------------------------------------------------
# Claude / OpenAI Prompt for generating synthetic conversations
# ---------------------------------------------------------------------------
SYNTHETIC_GENERATION_PROMPT = """You are generating training data for a Travel AI constraint extraction model.

Generate a realistic multi-turn conversation (6-12 turns) between a User and a Travel Assistant AI. The conversation should progressively reveal travel constraints.

## Rules:
1. The User should reveal constraints gradually (NOT all at once).
2. The Assistant should help with flights, hotels, dining, and itinerary.
3. Include at least ONE booking confirmation (hotel or flight) in the conversation.
4. Include natural variations: typos, abbreviations, informal language.
5. The Assistant sometimes uses tool calls like: <tool_call>{"name": "hotel_search", "arguments": {...}}
6. After the FULL conversation, output the final accumulated state as JSON.

## Output ConstraintDict Schema:
```json
{
    "budget": {"max_amount": <float>, "currency": "USD", "per_person": <bool>},
    "cities": ["<city1>", "<city2>"],
    "origin": "<origin_city or null>",
    "travel_dates": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
    "dietary": ["<restriction1>"],
    "passport": {"expiry_days": <int>, "visa_restriction": "<str>"},
    "travelers": {"adults": <int>, "children": <int>},
    "hotel_preferences": {"min_stars": <int>, "must_have": ["wifi", "pool"]},
    "booked_flights": [{"flight_code": "<XX1234>", "price": <float>}],
    "booked_hotels": [{"name": "<Hotel Name>", "stars": <int>, "price_per_night": <float>}]
}
```

Only include fields that were ACTUALLY mentioned or confirmed in the conversation.
Omit fields that were never discussed (e.g., if no passport was mentioned, omit "passport").

## Output Format:
Return a JSON object with TWO keys:
- "conversation": list of {"role": "user"|"assistant", "content": "..."}
- "constraints": the final ConstraintDict JSON

Generate ONE complete example now. Make it unique and realistic."""


# ---------------------------------------------------------------------------
# Predefined pools for MANUAL mode
# ---------------------------------------------------------------------------
CITIES = [
    "Paris", "London", "Rome", "Tokyo", "Dubai", "New York", "Barcelona",
    "Istanbul", "Bangkok", "Singapore", "Sydney", "Berlin", "Amsterdam",
    "Prague", "Vienna", "Seoul", "Mumbai", "Delhi", "Buenos Aires", "Cairo",
]

HOTELS = [
    ("The Ritz-Carlton", 5, 450.0),
    ("Le Meurice Hotel", 5, 380.0),
    ("Hotel de Crillon", 5, 520.0),
    ("Hilton Garden Inn", 4, 180.0),
    ("Marriott Courtyard", 4, 200.0),
    ("Holiday Inn Express", 3, 120.0),
    ("Novotel City Center", 4, 160.0),
    ("Four Seasons Resort", 5, 600.0),
    ("Hyatt Regency", 4, 220.0),
    ("Best Western Plus", 3, 95.0),
    ("Radisson Blu", 4, 190.0),
    ("InterContinental", 5, 350.0),
]

AIRLINES = [
    ("AF", "Air France"), ("BA", "British Airways"), ("LH", "Lufthansa"),
    ("EK", "Emirates"), ("SQ", "Singapore Airlines"), ("DL", "Delta"),
    ("UA", "United Airlines"), ("TK", "Turkish Airlines"), ("QR", "Qatar Airways"),
    ("AI", "Air India"),
]

DIETARY = ["vegan", "vegetarian", "halal", "kosher", "gluten-free", "pescatarian"]


def generate_manual_example():
    """Generate a single synthetic training example without any API."""

    origin = random.choice(CITIES)
    destinations = random.sample([c for c in CITIES if c != origin], k=random.randint(1, 3))
    budget = random.choice([1500, 2000, 2500, 3000, 4000, 5000, 8000, 10000])
    adults = random.choice([1, 1, 2, 2, 2, 3, 4])
    children = random.choice([0, 0, 0, 0, 1, 2])
    diet = random.choice(DIETARY + [None, None, None])  # 50% chance no dietary
    hotel = random.choice(HOTELS)
    airline_code, airline_name = random.choice(AIRLINES)
    flight_code = f"{airline_code}{random.randint(100, 9999)}"
    flight_price = random.choice([350, 450, 550, 680, 820, 1200, 1500])
    min_stars = random.choice([3, 4, 4, 5])
    start_month = random.randint(1, 12)
    start_day = random.randint(1, 28)
    duration = random.randint(3, 14)

    dest_str = " and ".join(destinations)
    travelers_str = f"{adults} adult{'s' if adults > 1 else ''}"
    if children:
        travelers_str += f" and {children} {'child' if children == 1 else 'children'}"

    # Build conversation
    conversation = [
        {"role": "user", "content": f"Hi, I want to plan a trip to {dest_str}"},
        {"role": "assistant", "content": f"I'd love to help you plan your trip to {dest_str}! Could you tell me your budget and travel dates?"},
        {"role": "user", "content": f"my budget is ${budget} and we are {travelers_str}. traveling from {origin}"},
        {"role": "assistant", "content": f"Great! A ${budget} budget for {travelers_str} from {origin} to {dest_str}. When would you like to travel?"},
        {"role": "user", "content": f"starting 2026-{start_month:02d}-{start_day:02d} for {duration} days"},
        {"role": "assistant", "content": f"Perfect! Let me search for flights and hotels for your {duration}-day trip."},
    ]

    if diet:
        conversation.extend([
            {"role": "user", "content": f"oh also i'm {diet} so keep that in mind for restaurants"},
            {"role": "assistant", "content": f"Noted! I'll make sure to find {diet}-friendly dining options."},
        ])

    # Hotel booking
    conversation.extend([
        {"role": "user", "content": "show me hotel options"},
        {"role": "assistant", "content": f"Here are some options:\n1. {hotel[0]} ({hotel[1]} stars, ${hotel[2]}/night)\n2. {HOTELS[(HOTELS.index(hotel) + 1) % len(HOTELS)][0]}\nWould you like to book one?"},
        {"role": "user", "content": "book the first one"},
        {"role": "assistant", "content": f"I've booked your stay at {hotel[0]} in {destinations[0]}. Enjoy your trip!"},
    ])

    # Flight booking
    conversation.extend([
        {"role": "user", "content": "now find flights"},
        {"role": "assistant", "content": f"I found a {airline_name} flight {flight_code} for ${flight_price}. Would you like to book it?"},
        {"role": "user", "content": "yes book it"},
        {"role": "assistant", "content": f"Done! Your flight {flight_code} with {airline_name} has been booked for ${flight_price}."},
    ])

    end_day = start_day + duration
    end_month = start_month
    if end_day > 28:
        end_day = end_day - 28
        end_month = min(start_month + 1, 12)

    # Build target constraints
    constraints = {
        "budget": {"max_amount": float(budget), "currency": "USD", "per_person": False},
        "cities": destinations,
        "origin": origin,
        "travel_dates": {
            "start": f"2026-{start_month:02d}-{start_day:02d}",
            "end": f"2026-{end_month:02d}-{end_day:02d}"
        },
        "travelers": {"adults": adults, "children": children},
        "hotel_preferences": {"min_stars": min_stars},
        "booked_flights": [{"flight_code": flight_code, "price": float(flight_price)}],
        "booked_hotels": [{"name": hotel[0], "stars": hotel[1], "price_per_night": hotel[2]}],
    }

    if diet:
        constraints["dietary"] = [diet]

    return conversation, constraints


def format_as_training_example(conversation, constraints):
    """
    Format a conversation + constraints into a chat-style training example.
    
    The model learns to output the constraint JSON as a structured response
    when given the conversation as context.
    """
    # Build the full conversation as context
    conv_text = ""
    for msg in conversation:
        role = "User" if msg["role"] == "user" else "Assistant"
        conv_text += f"{role}: {msg['content']}\n"

    system_prompt = (
        "You are a Travel AI State Tracker. Given a conversation between a User and a Travel Assistant, "
        "extract all travel constraints that were mentioned or confirmed during the conversation. "
        "Output ONLY a valid JSON object matching the ConstraintDict schema. "
        "Only include fields that were actually discussed. Omit empty or unmentioned fields."
    )

    training_example = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract the travel constraints from this conversation:\n\n{conv_text}"},
            {"role": "assistant", "content": json.dumps(constraints, indent=2)},
        ]
    }

    return training_example


def generate_manual_dataset(num_examples: int, output_path: str):
    """Generate a full dataset of manual examples."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    examples = []
    for _ in range(num_examples):
        conv, constraints = generate_manual_example()
        example = format_as_training_example(conv, constraints)
        examples.append(example)

    with open(output, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")

    print(f"Generated {num_examples} training examples -> {output}")
    return examples


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic training data")
    parser.add_argument("--mode", choices=["manual", "api"], default="manual",
                        help="manual: template-based, api: use LLM API")
    parser.add_argument("--output", default="training/data/train.jsonl",
                        help="Output JSONL path")
    parser.add_argument("--num", type=int, default=200,
                        help="Number of examples to generate")
    parser.add_argument("--provider", choices=["anthropic", "openai"], default="anthropic",
                        help="API provider for api mode")
    args = parser.parse_args()

    if args.mode == "manual":
        generate_manual_dataset(args.num, args.output)
    else:
        print("=" * 60)
        print("API MODE - Use the prompt below with Claude/GPT-4o-mini")
        print("=" * 60)
        print()
        print(SYNTHETIC_GENERATION_PROMPT)
        print()
        print("Copy the above prompt and run it in a loop via the API.")
        print(f"Set ANTHROPIC_API_KEY or OPENAI_API_KEY to use --mode api.")
        print(f"Each API call generates 1 example. You need ~{args.num} calls.")
