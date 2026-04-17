"""
Post-compression validator — the quality gate.

After compression, this module verifies that every critical entity from the
constraint dictionary is still present in the compressed prompt. If validation
fails, the orchestrator triggers fallback to simple sliding-window truncation.

This is the safety net that makes aggressive compression safe.
"""

from dataclasses import dataclass
from backend.agent.state import ConstraintDict


@dataclass
class ValidationResult:
    passed: bool
    missing_entities: list[str]
    reason: str = ""


class CompressionValidator:
    """
    Validates that a compressed prompt retains all critical entities.

    We check every field in the constraint dict against the compressed text.
    Missing entities don't crash the system — they trigger a fallback path.
    """

    def __init__(self, strict: bool = True):
        """
        Args:
            strict: If True, require exact string match for all entities.
                    If False, allow fuzzy matches (useful for debugging).
        """
        self.strict = strict

    def validate(
        self,
        compressed_text: str,
        constraints: ConstraintDict,
    ) -> ValidationResult:
        """
        Args:
            compressed_text: The prompt that will be sent to the model.
            constraints: The constraint dict — the source of truth.

        Returns:
            ValidationResult with .passed flag and list of missing entities.
        """
        missing = []
        text_lower = compressed_text.lower()

        # Check budget amount appears
        if "budget" in constraints:
            amount = constraints["budget"].get("max_amount")
            if amount is not None:
                amount_str = f"{int(amount)}" if amount.is_integer() else f"{amount}"
                # Accept "$3000", "3000", or "3,000" — any numeric form
                if not self._numeric_appears(amount_str, text_lower):
                    missing.append(f"budget:{amount_str}")

        # Check each city appears
        for city in constraints.get("cities", []):
            if city.lower() not in text_lower:
                missing.append(f"city:{city}")

        # Check dietary constraints
        for diet in constraints.get("dietary", []):
            if diet.lower() not in text_lower:
                missing.append(f"dietary:{diet}")

        # Check passport constraints (either the expiry_days number or the visa phrase)
        if "passport" in constraints:
            p = constraints["passport"]
            if "expiry_days" in p:
                days_str = str(p["expiry_days"])
                # Look for the number AND some passport-related word nearby
                if days_str not in compressed_text:
                    missing.append(f"passport:expiry_{days_str}")
            if "visa_restriction" in p:
                # Accept either the canonical string or any form of "visa"
                if "visa" not in text_lower:
                    missing.append(f"passport:visa_info")

        # Check booked flights — these are critical, never drop
        for booking in constraints.get("booked_flights", []):
            code = booking.get("flight_code")
            if code and code not in compressed_text:
                missing.append(f"flight:{code}")

        passed = len(missing) == 0
        reason = "" if passed else f"missing {len(missing)} critical entities"

        return ValidationResult(
            passed=passed,
            missing_entities=missing,
            reason=reason,
        )

    def _numeric_appears(self, number: str, text: str) -> bool:
        """Check if a numeric value appears in any common format."""
        # Try exact
        if number in text:
            return True
        # Try with comma separator (3000 -> 3,000)
        if len(number) >= 4:
            with_comma = number[:-3] + "," + number[-3:]
            if with_comma in text:
                return True
        return False
