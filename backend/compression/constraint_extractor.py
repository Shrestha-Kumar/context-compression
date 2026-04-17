"""
Deterministic constraint extraction.

This module replaces the LLM-based summarization from the original blueprint.
It uses regex and pattern matching to extract structured data from messages
and merge it into the persistent constraint dictionary.

Design principle: every critical constraint identified here becomes part of
the permanent system prompt prefix. It survives all compression stages. This
is what guarantees the needle test passes regardless of how aggressive
token pruning becomes on conversational history.
"""

import re
from typing import Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage

from backend.agent.state import ConstraintDict, empty_constraints


# -----------------------------------------------------------------------------
# City gazetteer
# -----------------------------------------------------------------------------
# A short list covering major travel destinations. In a production system this
# would come from a proper geodatabase; for the hackathon, this is sufficient.

KNOWN_CITIES = {
    # Europe
    "Paris", "London", "Rome", "Madrid", "Barcelona", "Berlin", "Munich",
    "Amsterdam", "Vienna", "Prague", "Budapest", "Athens", "Lisbon", "Dublin",
    "Copenhagen", "Stockholm", "Oslo", "Helsinki", "Zurich", "Geneva", "Milan",
    "Florence", "Venice", "Naples", "Lyon", "Marseille", "Nice", "Brussels",
    "Warsaw", "Krakow",
    # Asia
    "Tokyo", "Osaka", "Kyoto", "Seoul", "Beijing", "Shanghai", "Hong Kong",
    "Singapore", "Bangkok", "Hanoi", "Mumbai", "Delhi", "Bangalore", "Chennai",
    "Dubai", "Abu Dhabi", "Istanbul", "Jerusalem", "Kuala Lumpur", "Jakarta",
    "Manila", "Taipei",
    # Americas
    "New York", "Los Angeles", "San Francisco", "Chicago", "Boston", "Miami",
    "Washington", "Seattle", "Toronto", "Vancouver", "Montreal", "Mexico City",
    "Havana", "Rio de Janeiro", "Buenos Aires", "Lima", "Santiago",
    # Oceania & Africa
    "Sydney", "Melbourne", "Auckland", "Cape Town", "Cairo", "Marrakech",
    "Nairobi", "Johannesburg",
}


# -----------------------------------------------------------------------------
# Regex patterns
# -----------------------------------------------------------------------------

# Budget: "$3000", "3000 dollars", "USD 3000", "€2500", "budget of 4000"
BUDGET_PATTERNS = [
    # $3000 or $3,000 — grab the whole run of digits+commas, strip commas later
    re.compile(r"\$\s*([\d,]+)", re.IGNORECASE),
    re.compile(r"(\d{3,6})\s*(?:dollars|usd)\b", re.IGNORECASE),
    re.compile(r"\busd\s*(\d{3,6})\b", re.IGNORECASE),
    re.compile(r"€\s*([\d,]+)"),
    re.compile(r"(\d{3,6})\s*(?:euros?|eur)\b", re.IGNORECASE),
    re.compile(r"budget\s+(?:of|is|under|below|around)?\s*\$?\s*([\d,]+)", re.IGNORECASE),
]

# Dietary: keywords that indicate dietary restrictions
DIETARY_KEYWORDS = {
    "vegan": "vegan",
    "vegetarian": "vegetarian",
    "veg ": "vegetarian",
    "halal": "halal",
    "kosher": "kosher",
    "gluten-free": "gluten-free",
    "gluten free": "gluten-free",
    "dairy-free": "dairy-free",
    "nut allergy": "nut-allergy",
    "peanut allergy": "nut-allergy",
    "pescatarian": "pescatarian",
}

# Passport: "passport expires in X days", "visa on arrival", etc.
PASSPORT_EXPIRY = re.compile(
    r"passport\s+(?:expires?|expiry|valid(?:ity)?)(?:\s+\w+){0,3}?\s+(\d+)\s*days?",
    re.IGNORECASE,
)
VISA_ON_ARRIVAL = re.compile(
    r"(?:visa[- ]on[- ]arrival|visa on arrival|voa only|visa free)",
    re.IGNORECASE,
)

# Travelers: "2 adults", "family of 4", "solo traveler"
TRAVELERS_ADULTS = re.compile(r"(\d+)\s+adults?", re.IGNORECASE)
TRAVELERS_CHILDREN = re.compile(r"(\d+)\s+(?:child(?:ren)?|kids?)", re.IGNORECASE)
SOLO_TRAVELER = re.compile(r"\b(?:solo traveler|solo trip|traveling alone|by myself)\b", re.IGNORECASE)

# Dates: "May 1st", "May 1-14", "2026-05-01", "starting June 3"
DATE_ISO = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
DATE_RANGE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:\s*[-–to]+\s*(\d{1,2}))?",
    re.IGNORECASE,
)

# Hotel preferences
HOTEL_STARS = re.compile(r"(\d)[- ]star\s+hotel", re.IGNORECASE)

# City change patterns: "change Paris to Lyon", "swap Rome for Milan"
CITY_CHANGE = re.compile(
    r"(?:change|swap|replace)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+(?:to|for|with)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)",
)


# -----------------------------------------------------------------------------
# Extractor class
# -----------------------------------------------------------------------------

class ConstraintExtractor:
    """
    Stateful extractor: applies pattern matching to new messages and merges
    findings into the running constraint dictionary.

    Call `update(state_constraints, new_messages)` after every user turn.
    """

    def update(
        self,
        current: ConstraintDict,
        messages: list[BaseMessage],
    ) -> ConstraintDict:
        """
        Merge extractions from all messages into the running constraint dict.
        Returns a new dict — does not mutate the input.
        """
        result = dict(current)  # shallow copy
        # Ensure required list fields exist
        result.setdefault("cities", [])
        result.setdefault("dietary", [])
        result.setdefault("booked_flights", [])
        result.setdefault("booked_hotels", [])

        for msg in messages:
            text = self._message_text(msg)
            if not text:
                continue

            # Only human messages carry constraint intent
            if isinstance(msg, HumanMessage):
                self._extract_budget(text, result)
                self._extract_dietary(text, result)
                self._extract_passport(text, result)
                self._extract_travelers(text, result)
                self._extract_cities(text, result)
                self._extract_city_changes(text, result)
                self._extract_dates(text, result)
                self._extract_hotels(text, result)

            # Tool messages may carry booking confirmations
            elif isinstance(msg, ToolMessage):
                self._extract_bookings(text, result)

        # Dedupe cities while preserving order (swaps can create duplicates
        # when both old and new city names appear in the same message)
        if result.get("cities"):
            seen = set()
            deduped = []
            for city in result["cities"]:
                if city not in seen:
                    deduped.append(city)
                    seen.add(city)
            result["cities"] = deduped

        return result

    # ------------------------------------------------------------------
    # Individual extractors
    # ------------------------------------------------------------------

    def _extract_budget(self, text: str, out: ConstraintDict) -> None:
        # Skip per-night/per-day amounts — those are hotel rates, not total budget
        text_lower = text.lower()
        for pattern in BUDGET_PATTERNS:
            match = pattern.search(text)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    amount = float(amount_str)
                    # Reject if this match is immediately followed by /night, per night, a night
                    tail = text[match.end():match.end() + 20].lower()
                    if re.match(r"\s*(?:/|per\s+|a\s+)(?:night|day|person)", tail):
                        continue
                    # Sanity check: travel budgets are typically $100-$100,000
                    if 100 <= amount <= 100_000:
                        # Don't overwrite a much larger existing budget with a smaller one
                        existing = out.get("budget", {}).get("max_amount", 0)
                        if existing and amount < existing * 0.25:
                            continue
                        currency = "EUR" if "€" in text or "euro" in text_lower else "USD"
                        out["budget"] = {
                            "max_amount": amount,
                            "currency": currency,
                            "per_person": "per person" in text_lower,
                        }
                        return
                except ValueError:
                    continue

    def _extract_dietary(self, text: str, out: ConstraintDict) -> None:
        text_lower = text.lower()
        for keyword, canonical in DIETARY_KEYWORDS.items():
            if keyword in text_lower:
                if canonical not in out["dietary"]:
                    out["dietary"].append(canonical)

    def _extract_passport(self, text: str, out: ConstraintDict) -> None:
        passport = dict(out.get("passport", {}))

        expiry_match = PASSPORT_EXPIRY.search(text)
        if expiry_match:
            passport["expiry_days"] = int(expiry_match.group(1))

        if VISA_ON_ARRIVAL.search(text):
            passport["visa_restriction"] = "visa_on_arrival_only"

        if passport:
            out["passport"] = passport

    def _extract_travelers(self, text: str, out: ConstraintDict) -> None:
        travelers = dict(out.get("travelers", {}))

        if SOLO_TRAVELER.search(text):
            travelers["adults"] = 1
            travelers["children"] = 0
        else:
            adults_match = TRAVELERS_ADULTS.search(text)
            children_match = TRAVELERS_CHILDREN.search(text)
            if adults_match:
                travelers["adults"] = int(adults_match.group(1))
            if children_match:
                travelers["children"] = int(children_match.group(1))

        if travelers:
            out["travelers"] = travelers

    def _extract_cities(self, text: str, out: ConstraintDict) -> None:
        """Match any known cities in the text and add them to the itinerary."""
        for city in KNOWN_CITIES:
            # Word-boundary match to avoid "Rome" matching "Romeo"
            if re.search(rf"\b{re.escape(city)}\b", text):
                if city not in out["cities"]:
                    out["cities"].append(city)

    def _extract_city_changes(self, text: str, out: ConstraintDict) -> None:
        """Handle "change Paris to Lyon" patterns — swap in the city list."""
        for match in CITY_CHANGE.finditer(text):
            old_city = match.group(1).strip()
            new_city = match.group(2).strip()
            if old_city in out["cities"] and new_city in KNOWN_CITIES:
                idx = out["cities"].index(old_city)
                out["cities"][idx] = new_city

    def _extract_dates(self, text: str, out: ConstraintDict) -> None:
        dates = dict(out.get("travel_dates", {}))

        iso_matches = DATE_ISO.findall(text)
        if iso_matches:
            if len(iso_matches) >= 2:
                dates["start"] = iso_matches[0]
                dates["end"] = iso_matches[1]
            else:
                dates["start"] = iso_matches[0]

        range_match = DATE_RANGE.search(text)
        if range_match and "start" not in dates:
            month = range_match.group(1)
            start_day = range_match.group(2)
            end_day = range_match.group(3)
            dates["mentioned"] = f"{month} {start_day}" + (
                f"-{end_day}" if end_day else ""
            )

        if dates:
            out["travel_dates"] = dates

    def _extract_hotels(self, text: str, out: ConstraintDict) -> None:
        hotels = dict(out.get("hotel_preferences", {}))

        stars_match = HOTEL_STARS.search(text)
        if stars_match:
            hotels["min_stars"] = int(stars_match.group(1))

        if hotels:
            out["hotel_preferences"] = hotels

    def _extract_bookings(self, text: str, out: ConstraintDict) -> None:
        """Parse structured booking confirmations from tool outputs."""
        # Flight code pattern: AF1234, UA123, LH2345
        flight_match = re.search(r'"flight_code"\s*:\s*"([A-Z]{2,3}\d{3,4})"', text)
        price_match = re.search(r'"price"\s*:\s*(\d+(?:\.\d+)?)', text)

        if flight_match and '"confirmed": true' in text:
            booking = {"flight_code": flight_match.group(1)}
            if price_match:
                booking["price"] = float(price_match.group(1))
            if booking not in out["booked_flights"]:
                out["booked_flights"].append(booking)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _message_text(self, msg: BaseMessage) -> Optional[str]:
        content = msg.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            # Multimodal messages — extract text parts
            return " ".join(
                part.get("text", "") for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            )
        return None


# -----------------------------------------------------------------------------
# Formatting for system prompt injection
# -----------------------------------------------------------------------------

def format_constraints_as_prompt(constraints: ConstraintDict) -> str:
    """
    Render the constraint dict as a compact system prompt prefix.
    This is what gets prepended to every model call — the agent always sees
    this regardless of how aggressive compression becomes.

    Target: under 300 tokens.
    """
    lines = ["[USER CONSTRAINTS — MUST BE RESPECTED]"]

    if "budget" in constraints:
        b = constraints["budget"]
        suffix = " per person" if b.get("per_person") else " total"
        lines.append(f"- Budget: {b['currency']} {b['max_amount']:.0f}{suffix}")

    if constraints.get("cities"):
        lines.append(f"- Itinerary: {' → '.join(constraints['cities'])}")

    if constraints.get("origin"):
        lines.append(f"- Origin: {constraints['origin']}")

    if constraints.get("travel_dates"):
        d = constraints["travel_dates"]
        if "start" in d and "end" in d:
            lines.append(f"- Dates: {d['start']} to {d['end']}")
        elif "mentioned" in d:
            lines.append(f"- Dates mentioned: {d['mentioned']}")

    if constraints.get("dietary"):
        lines.append(f"- Dietary: {', '.join(constraints['dietary'])}")

    if "passport" in constraints:
        p = constraints["passport"]
        parts = []
        if "expiry_days" in p:
            parts.append(f"expires in {p['expiry_days']} days")
        if "visa_restriction" in p:
            parts.append(p["visa_restriction"].replace("_", " "))
        if parts:
            lines.append(f"- Passport: {'; '.join(parts)}")

    if "travelers" in constraints:
        t = constraints["travelers"]
        lines.append(
            f"- Travelers: {t.get('adults', 1)} adults, "
            f"{t.get('children', 0)} children"
        )

    if "hotel_preferences" in constraints:
        h = constraints["hotel_preferences"]
        if "min_stars" in h:
            lines.append(f"- Hotels: minimum {h['min_stars']} stars")

    if constraints.get("booked_flights"):
        codes = [f["flight_code"] for f in constraints["booked_flights"]]
        lines.append(f"- Booked flights: {', '.join(codes)}")

    return "\n".join(lines) if len(lines) > 1 else ""
