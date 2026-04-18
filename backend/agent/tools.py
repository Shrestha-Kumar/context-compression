"""
Mock travel APIs.

These are deterministic stubs that return realistic verbose JSON payloads.
The verbosity is intentional — it creates the context pressure that
demonstrates compression need.

In a real system these would hit actual APIs (Amadeus, Booking.com, etc).
For the hackathon, deterministic mocks are preferable: reproducible demos,
no API keys, no rate limits.
"""

import json
import random
from typing import Any
from langchain_core.tools import tool


# Seed for reproducible outputs during the demo
_RNG = random.Random(42)


# -----------------------------------------------------------------------------
# Flight search
# -----------------------------------------------------------------------------

# Airline name → code mapping. Used to generate realistic flight codes.
AIRLINES = [
    ("Air France", "AF"), ("Lufthansa", "LH"), ("British Airways", "BA"),
    ("Emirates", "EK"), ("Singapore Airlines", "SQ"), ("KLM", "KL"),
    ("United Airlines", "UA"), ("Delta Air Lines", "DL"),
    ("American Airlines", "AA"), ("Qatar Airways", "QR"),
    ("Turkish Airlines", "TK"), ("Cathay Pacific", "CX"),
]


from duckduckgo_search import DDGS
from datetime import datetime

@tool
def flight_search(origin: str, destination: str, date: str) -> str:
    """Search for flights over the open internet via DDGS."""
    try:
        query = f"flights from {origin} to {destination} on {date} cheap tickets price"
        results = DDGS().text(query, max_results=3)
        return json.dumps({
            "live_search_source": "DuckDuckGo Internet Extraction",
            "query": query,
            "results": results
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "message": "Verify internet connection"})

@tool
def hotel_search(city: str, check_in: str, check_out: str, min_stars: int = 3) -> str:
    """Search for real hotels via the open internet using DDGS."""
    try:
        query = f"best hotels in {city} {min_stars} stars {check_in} to {check_out} rates booking"
        results = DDGS().text(query, max_results=3)
        return json.dumps({
            "live_search_source": "DuckDuckGo Internet Extraction",
            "query": query,
            "results": results
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# -----------------------------------------------------------------------------
# Restaurant search
# -----------------------------------------------------------------------------

CUISINE_TYPES = [
    "Italian", "French", "Japanese", "Indian", "Thai", "Mediterranean",
    "Mexican", "Chinese", "American", "Middle Eastern", "Vietnamese", "Korean",
]


@tool
def restaurant_search(city: str, cuisine: str = "any", dietary: str = "none") -> str:
    """
    Search for restaurants in a city, optionally filtered by cuisine and dietary needs.

    Args:
        city: City name
        cuisine: Cuisine type filter, or "any"
        dietary: Dietary restriction filter (e.g. "vegan", "halal"), or "none"

    Returns:
        JSON string with restaurant options.
    """
    rng = random.Random(f"{city}-{cuisine}-{dietary}-restaurants")
    num_options = rng.randint(3, 5)
    options = []
    for i in range(num_options):
        cuisine_name = cuisine if cuisine != "any" else rng.choice(CUISINE_TYPES)
        options.append({
            "restaurant_id": f"R{rng.randint(10000, 99999)}",
            "name": f"{rng.choice(['Le', 'La', 'Il', 'The', 'Chez'])} {rng.choice(['Jardin', 'Soleil', 'Verde', 'Luna', 'Nova'])}",
            "city": city,
            "cuisine": cuisine_name,
            "rating": round(3.8 + rng.random() * 1.2, 1),
            "reviews_count": rng.randint(80, 2400),
            "price_level": rng.choice(["$", "$$", "$$$", "$$$$"]),
            "supports_dietary": [dietary] if dietary != "none" else [],
            "opening_hours": "11:00-23:00",
            "reservation_required": rng.choice([True, False]),
            "address": f"{rng.randint(1, 100)} {rng.choice(['Rue', 'Via', 'Street'])} {rng.choice(['Victor', 'Rivoli', 'Roma', 'Oak'])}",
        })

    return json.dumps({
        "query": {"city": city, "cuisine": cuisine, "dietary": dietary},
        "total_results": num_options,
        "options": options,
    }, indent=2)


# -----------------------------------------------------------------------------
# Visa / travel advisory lookup
# -----------------------------------------------------------------------------

# Minimal static database for visa requirements
VISA_DATA = {
    "Japan": {"visa_on_arrival": False, "min_passport_validity_months": 6},
    "Thailand": {"visa_on_arrival": True, "min_passport_validity_months": 6},
    "Indonesia": {"visa_on_arrival": True, "min_passport_validity_months": 6},
    "Cambodia": {"visa_on_arrival": True, "min_passport_validity_months": 6},
    "Nepal": {"visa_on_arrival": True, "min_passport_validity_months": 6},
    "UAE": {"visa_on_arrival": True, "min_passport_validity_months": 6},
    "Egypt": {"visa_on_arrival": True, "min_passport_validity_months": 6},
    "Kenya": {"visa_on_arrival": True, "min_passport_validity_months": 6},
    "Turkey": {"visa_on_arrival": True, "min_passport_validity_months": 6},
    "Georgia": {"visa_on_arrival": True, "min_passport_validity_months": 3},
    "France": {"visa_on_arrival": False, "min_passport_validity_months": 6},
    "Germany": {"visa_on_arrival": False, "min_passport_validity_months": 6},
    "Italy": {"visa_on_arrival": False, "min_passport_validity_months": 6},
    "Spain": {"visa_on_arrival": False, "min_passport_validity_months": 6},
    "UK": {"visa_on_arrival": False, "min_passport_validity_months": 6},
    "USA": {"visa_on_arrival": False, "min_passport_validity_months": 6},
}


@tool
def visa_requirements(country: str) -> str:
    """
    Look up visa requirements for a destination country.

    Args:
        country: Country name

    Returns:
        JSON string with visa/passport requirements.
    """
    info = VISA_DATA.get(country)
    if info is None:
        info = {
            "visa_on_arrival": False,
            "min_passport_validity_months": 6,
            "note": "Data unavailable — check with embassy",
        }
    return json.dumps({
        "country": country,
        "visa_on_arrival": info["visa_on_arrival"],
        "min_passport_validity_months": info["min_passport_validity_months"],
        "general_note": (
            "Travelers should confirm requirements with the embassy before departure. "
            "Rules can change based on nationality and purpose of visit."
        ),
    }, indent=2)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _add_minutes(hour: int, minute: int, add: int) -> str:
    total = hour * 60 + minute + add
    new_hour = (total // 60) % 24
    new_min = total % 60
    return f"{new_hour:02d}:{new_min:02d}"


# -----------------------------------------------------------------------------
# Export list for the agent
# -----------------------------------------------------------------------------

ALL_TOOLS = [flight_search, hotel_search, restaurant_search, visa_requirements]
TOOL_MAP = {t.name: t for t in ALL_TOOLS}
