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


@tool
def flight_search(origin: str, destination: str, date: str) -> str:
    """
    Search for flights between two cities on a given date.

    Args:
        origin: Origin city name (e.g. "Paris")
        destination: Destination city name (e.g. "Rome")
        date: ISO date string (e.g. "2026-05-01")

    Returns:
        JSON string with flight options.
    """
    rng = random.Random(f"{origin}-{destination}-{date}")
    num_options = rng.randint(3, 6)
    options = []
    for i in range(num_options):
        airline_name, airline_code = rng.choice(AIRLINES)
        flight_num = rng.randint(100, 9999)
        departure_hour = rng.randint(5, 22)
        duration_min = rng.randint(90, 720)
        price_usd = rng.randint(120, 850)
        stops = rng.choice([0, 0, 0, 1, 1, 2])

        options.append({
            "flight_code": f"{airline_code}{flight_num}",
            "airline": airline_name,
            "origin": origin,
            "destination": destination,
            "date": date,
            "departure_time": f"{departure_hour:02d}:{rng.randint(0, 59):02d}",
            "arrival_time": _add_minutes(departure_hour, rng.randint(0, 59), duration_min),
            "duration_minutes": duration_min,
            "stops": stops,
            "aircraft_type": rng.choice(["Boeing 737-800", "Airbus A320", "Airbus A350", "Boeing 787"]),
            "cabin_class": "economy",
            "baggage_allowance_kg": rng.choice([20, 23, 25, 30]),
            "refundable": rng.choice([True, False]),
            "price": price_usd,
            "currency": "USD",
            "available_seats": rng.randint(1, 40),
        })

    return json.dumps({
        "query": {"origin": origin, "destination": destination, "date": date},
        "total_results": num_options,
        "options": options,
    }, indent=2)


# -----------------------------------------------------------------------------
# Hotel search
# -----------------------------------------------------------------------------

HOTEL_BRANDS = [
    "Grand Palace", "City Center Inn", "Boutique Haven", "Royal Plaza",
    "Luxury Suites", "Comfort Stay", "Heritage Hotel", "Skyline Tower",
    "Garden View", "Metropolitan", "Riverside", "Executive Suites",
]


@tool
def hotel_search(city: str, check_in: str, check_out: str, min_stars: int = 3) -> str:
    """
    Search for hotels in a city.

    Args:
        city: City name (e.g. "Paris")
        check_in: ISO date string
        check_out: ISO date string
        min_stars: Minimum star rating (1-5)

    Returns:
        JSON string with hotel options.
    """
    rng = random.Random(f"{city}-{check_in}-hotels")
    num_options = rng.randint(4, 7)
    options = []
    for i in range(num_options):
        brand = rng.choice(HOTEL_BRANDS)
        stars = rng.randint(max(min_stars, 1), 5)
        price_per_night = 40 + (stars * 35) + rng.randint(0, 60)

        options.append({
            "hotel_id": f"H{rng.randint(10000, 99999)}",
            "name": f"{brand} {city}",
            "city": city,
            "stars": stars,
            "rating": round(3.5 + rng.random() * 1.5, 1),
            "reviews_count": rng.randint(120, 5800),
            "address": f"{rng.randint(1, 200)} {rng.choice(['Main', 'Central', 'Park', 'Station'])} Street",
            "check_in": check_in,
            "check_out": check_out,
            "price_per_night": price_per_night,
            "currency": "USD",
            "amenities": rng.sample(
                ["wifi", "breakfast", "gym", "pool", "spa", "parking", "pet-friendly", "restaurant"],
                k=rng.randint(3, 6),
            ),
            "cancellation_policy": rng.choice(["free_until_24h", "free_until_48h", "non_refundable"]),
            "distance_to_center_km": round(rng.random() * 8, 1),
            "available_rooms": rng.randint(1, 12),
        })

    return json.dumps({
        "query": {"city": city, "check_in": check_in, "check_out": check_out, "min_stars": min_stars},
        "total_results": num_options,
        "options": options,
    }, indent=2)


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
