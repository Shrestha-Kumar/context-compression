"""
MultiWOZ → ConstraintDict Converter.

Downloads the MultiWOZ 2.4 dataset from Hugging Face and converts
the hotel/restaurant/train booking dialogues into our ConstraintDict
training format.

Usage:
    pip install datasets
    python training/convert_multiwoz.py --output training/data/multiwoz_converted.jsonl --max 300

This gives you ~300 real human conversations mapped to our schema,
which you can combine with the synthetic data for better diversity.
"""

import argparse
import json
import re
from pathlib import Path

from datasets import load_dataset


# ---------------------------------------------------------------------------
# Schema mapping: MultiWOZ slot names → our ConstraintDict fields
# ---------------------------------------------------------------------------

CITY_MAP = {
    "cambridge": "Cambridge",
    "london": "London",
    "birmingham": "Birmingham",
    "stansted": "London",
    "kings lynn": "Cambridge",
    "norwich": "Norwich",
    "peterborough": "Peterborough",
    "stevenage": "London",
    "ely": "Cambridge",
    "leicester": "Leicester",
    "broxbourne": "London",
}

DIETARY_MAP = {
    "chinese": None,
    "indian": None,
    "italian": None,
    "british": None,
    "european": None,
    "vegetarian": "vegetarian",
    "vegan": "vegan",
    "halal": "halal",
    "kosher": "kosher",
}


def extract_constraints_from_multiwoz(dialogue_acts, turns):
    """
    Convert MultiWOZ belief states into our ConstraintDict format.
    """
    constraints = {}
    cities = []
    booked_hotels = []
    booked_flights = []

    for turn in turns:
        # MultiWOZ stores belief state as slot-value pairs
        if "dialogue_acts" not in turn:
            continue

        text = turn.get("utterance", "").lower()

        # Extract cities from destination/departure slots
        for slot_key in ["train-destination", "train-departure", "hotel-name", "restaurant-area"]:
            if slot_key in turn.get("belief_state", {}):
                val = turn["belief_state"][slot_key].lower()
                mapped = CITY_MAP.get(val, val.title())
                if mapped and mapped not in cities:
                    cities.append(mapped)

        # Extract hotel info
        if "hotel-name" in turn.get("belief_state", {}):
            name = turn["belief_state"]["hotel-name"]
            if name and name != "not mentioned":
                stars = turn.get("belief_state", {}).get("hotel-stars", "0")
                try:
                    stars = int(stars)
                except (ValueError, TypeError):
                    stars = 0
                hotel = {"name": name.title(), "stars": stars}
                if hotel not in booked_hotels:
                    booked_hotels.append(hotel)

        # Extract dietary from restaurant food type
        food = turn.get("belief_state", {}).get("restaurant-food", "")
        if food and food in DIETARY_MAP and DIETARY_MAP[food]:
            if "dietary" not in constraints:
                constraints["dietary"] = []
            if DIETARY_MAP[food] not in constraints["dietary"]:
                constraints["dietary"].append(DIETARY_MAP[food])

        # Extract traveler count
        people = turn.get("belief_state", {}).get("hotel-people", "")
        if people and people != "not mentioned":
            try:
                constraints["travelers"] = {"adults": int(people), "children": 0}
            except (ValueError, TypeError):
                pass

        # Extract dates
        day = turn.get("belief_state", {}).get("hotel-day", "")
        stay = turn.get("belief_state", {}).get("hotel-stay", "")
        if day and day != "not mentioned":
            constraints.setdefault("travel_dates", {})["start"] = day
            if stay and stay != "not mentioned":
                try:
                    constraints["travel_dates"]["duration_nights"] = int(stay)
                except (ValueError, TypeError):
                    pass

    if cities:
        constraints["cities"] = cities
    if booked_hotels:
        constraints["booked_hotels"] = booked_hotels
    if booked_flights:
        constraints["booked_flights"] = booked_flights

    return constraints


def convert_multiwoz_simple(max_examples: int, output_path: str):
    """
    Simplified converter that works with the standard MultiWOZ HF format.
    Extracts constraints from the dialogue text using pattern matching.
    """
    logger_info = print

    logger_info(f"Loading MultiWOZ 2.2 from Hugging Face...")
    dataset = load_dataset("tuetschek/multi_woz_v22", split="train")

    logger_info(f"Loaded {len(dataset)} dialogues")

    system_prompt = (
        "You are a Travel AI State Tracker. Given a conversation between a User and a Travel Assistant, "
        "extract all travel constraints that were mentioned or confirmed during the conversation. "
        "Output ONLY a valid JSON object matching the ConstraintDict schema. "
        "Only include fields that were actually discussed. Omit empty or unmentioned fields."
    )

    examples = []
    count = 0

    for item in dataset:
        if count >= max_examples:
            break

        turns = item.get("turns", {})
        if not turns:
            continue

        # Build conversation text
        utterances = turns.get("utterance", [])
        speakers = turns.get("speaker", [])
        
        if not utterances or len(utterances) < 4:
            continue

        # Extract constraints from text using simple patterns
        full_text = " ".join(utterances)
        constraints = {}

        # Cities from text
        city_keywords = ["cambridge", "london", "birmingham", "norwich", "peterborough"]
        found_cities = []
        for city in city_keywords:
            if city in full_text.lower():
                found_cities.append(city.title())
        if found_cities:
            constraints["cities"] = list(set(found_cities))

        # Hotel stars
        stars_match = re.search(r"(\d)\s*star", full_text.lower())
        if stars_match:
            constraints["hotel_preferences"] = {"min_stars": int(stars_match.group(1))}

        # People count
        people_match = re.search(r"(\d+)\s*(?:people|person|guests?|adult)", full_text.lower())
        if people_match:
            constraints["travelers"] = {"adults": int(people_match.group(1)), "children": 0}

        # Price range
        price_match = re.search(r"(?:cheap|moderate|expensive)", full_text.lower())
        if price_match:
            price_map = {"cheap": 100, "moderate": 200, "expensive": 400}
            constraints["budget"] = {
                "max_amount": float(price_map.get(price_match.group(0), 200)),
                "currency": "GBP",
                "per_person": False,
            }

        # Skip if too few constraints extracted
        if len(constraints) < 2:
            continue

        # Build conversation
        conv_text = ""
        for utt, spk in zip(utterances, speakers):
            role = "User" if spk == 0 else "Assistant"
            conv_text += f"{role}: {utt}\n"

        example = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract the travel constraints from this conversation:\n\n{conv_text}"},
                {"role": "assistant", "content": json.dumps(constraints, indent=2)},
            ]
        }
        examples.append(example)
        count += 1

    # Save
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")

    logger_info(f"Converted {len(examples)} MultiWOZ dialogues -> {output}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert MultiWOZ to ConstraintDict format")
    parser.add_argument("--output", default="training/data/multiwoz_converted.jsonl")
    parser.add_argument("--max", type=int, default=300, help="Max examples to convert")
    args = parser.parse_args()

    convert_multiwoz_simple(args.max, args.output)
