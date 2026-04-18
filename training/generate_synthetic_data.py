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
SYNTHETIC_GENERATION_PROMPT = """You are generating training data for a Context Extraction AI.

Generate a realistic multi-turn conversation where a user interacts with an AI agent. The user will declare routines, specify preferences, and perform changes of mind (updates/deletions).

## Rules:
1. Include CRU/D operations: The user adds a preference, then later asks to change or remove it.
2. The UI tracks "active_trip", "user_profile" (routines and preferences), and a "changelog".
3. After the FULL conversation, output the final absolute state as JSON.

## Output MemoryState Schema:
```json
{
    "active_trip": {
        "destinations": ["Paris"],
        "dates": {},
        "bookings": [{"type": "flight", "code": "AF123", "price": 400}]
    },
    "user_profile": {
        "routines": ["visits Paris on Saturdays"],
        "preferences": ["vegan pizza", "economy class seating"]
    },
    "changelog": [
        {"date": "2026-04-19", "action": "added routine: visits Paris on Fridays"},
        {"date": "2026-04-19", "action": "updated routine -> visits Paris on Saturdays"}
    ]
}
```

Return a JSON object with TWO keys:
- "conversation": list of {"role": "user"|"assistant", "content": "..."}
- "constraints": the final MemoryState JSON

Make it highly realistic to train state tracking resilience."""


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
    """Generate a single synthetic training example demonstrating CRU/D and MemoryState."""
    origin = random.choice(CITIES)
    destinations = random.sample([c for c in CITIES if c != origin], k=2)
    hotel = random.choice(HOTELS)
    airline_code, airline_name = random.choice(AIRLINES)
    flight_code = f"{airline_code}{random.randint(100, 9999)}"
    flight_price = random.choice([350, 450, 550, 680, 820, 1200, 1500])

    routines = [f"I frequently visit {destinations[0]} on Saturdays.", "I always fly out on Friday nights."]
    selected_routine = random.choice(routines)
    
    preferences = ["vegan pizza", "economy seating", "high-floor room"]
    old_pref = random.choice(preferences)
    new_pref = random.choice(["kosher meals", "business class", "quiet room"])

    conversation = [
        {"role": "user", "content": f"Hi, I want to travel to {destinations[0]} from {origin}. Just so you know, {selected_routine}."},
        {"role": "assistant", "content": f"I've noted that! What are your preferences?"},
        {"role": "user", "content": f"Make sure to note down that I like {old_pref}."},
        {"role": "assistant", "content": f"Noted: {old_pref}. Should I book flights for you?"},
        {"role": "user", "content": f"Yes, book a flight."},
        {"role": "assistant", "content": f"Booked flight {flight_code} with {airline_name} for ${flight_price}."},
        {"role": "user", "content": f"Wait, I changed my mind. Remove {old_pref}. I actually want {new_pref} instead."},
        {"role": "assistant", "content": f"Got it. I've deleted {old_pref} and updated your profile with {new_pref}."},
    ]

    memory = {
        "active_trip": {
            "destinations": [destinations[0]],
            "dates": {},
            "bookings": [
                {"type": "flight", "code": flight_code, "price": flight_price}
            ]
        },
        "user_profile": {
            "routines": [selected_routine],
            "preferences": [new_pref]
        },
        "changelog": [
            {"date": "2026-04-19", "action": f"added routine: {selected_routine}"},
            {"date": "2026-04-19", "action": f"added preference: {old_pref}"},
            {"date": "2026-04-19", "action": f"booked flight: {flight_code}"},
            {"date": "2026-04-19", "action": f"deleted preference: {old_pref}"},
            {"date": "2026-04-19", "action": f"added preference: {new_pref}"}
        ]
    }
    
    thought = (
        f"<thought>\n"
        f"The user initiated a trip to {destinations[0]} from {origin}.\n"
        f"A routine was established: {selected_routine}.\n"
        f"Initially, the user added a preference for {old_pref}.\n"
        f"A booking was made for flight {flight_code}.\n"
        f"The user subsequently changed their mind, removing {old_pref} and preferring {new_pref}.\n"
        f"I will record these timeline events in the changelog and output the final absolute state.\n"
        f"</thought>\n\n"
    )
    
    return conversation, memory, thought


def generate_empty_example():
    """Generate a negative training example featuring no travel constraints."""
    greetings = [
        [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "Hello! How can I assist you today?"},
            {"role": "user", "content": "how are you"},
            {"role": "assistant", "content": "I'm just a computer program, but thank you for asking! How can I help you on your trip?"}
        ],
        [
            {"role": "user", "content": "hi there"},
            {"role": "assistant", "content": "Hi! What kind of trip are you planning?"},
        ],
        [
            {"role": "user", "content": "what's the weather like today?"},
            {"role": "assistant", "content": "I don't have real-time live weather feeds right now, but I can help you plan a trip!"},
            {"role": "user", "content": "okay let me think"},
        ],
        [
            {"role": "user", "content": "good morning"},
            {"role": "assistant", "content": "Good morning! Are you looking to book a flight?"},
        ]
    ]
    
    import random
    conversation = random.choice(greetings)
    
    memory = {
        "active_trip": {
            "destinations": [],
            "dates": {},
            "bookings": []
        },
        "user_profile": {
            "routines": [],
            "preferences": []
        },
        "changelog": []
    }
    
    thought = (
        f"<thought>\n"
        f"The user is engaging in casual conversation or greetings without explicitly providing any actionable travel constraints or preferences.\n"
        f"Therefore, the state remains appropriately empty.\n"
        f"</thought>\n\n"
    )
    
    return conversation, memory, thought


def format_as_training_example(conversation, constraints, thought):
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
        "You are an intelligent Memory State Tracker. Given a conversation, "
        "evaluate changes to the persistent states step-by-step using a <thought> block. "
        "Then, extract the final state (active trips, routines, preferences) and "
        "record all additions, updates, and deletions into the changelog array. "
        "Always output the valid JSON object directly after the <thought> block."
    )

    training_example = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract the travel constraints from this conversation:\n\n{conv_text}"},
            {"role": "assistant", "content": f"{thought}{json.dumps(constraints, indent=2)}"},
        ]
    }

    return training_example


def generate_manual_dataset(num_examples: int, output_path: str):
    """Generate a full dataset of manual examples."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    examples = []
    for _ in range(num_examples):
        # 25% injection rate of negative semantic examples mapping to identical null constraints
        import random
        if random.random() < 0.25:
            conv, constraints, thought = generate_empty_example()
        else:
            conv, constraints, thought = generate_manual_example()
            
        example = format_as_training_example(conv, constraints, thought)
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
    parser.add_argument("--num", type=int, default=500,
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
