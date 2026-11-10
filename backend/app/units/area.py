"""Area conversion helpers using Decimal arithmetic exclusively.

Never use float for area or property measurements per AGENTS.md Hard Rule 8.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

# Exact conversion factors agreed for Maharashtra property registry
# 1 Sq. Mtr = 10.7639104 Sq. Ft. (Rounded to 4 decimal places for statutory calculation)
SQM_TO_SQFT_FACTOR = Decimal("10.7639")
GUNTHA_TO_SQFT_FACTOR = Decimal("1089.00")
HECTARE_TO_SQM_FACTOR = Decimal("10000.00")
ARE_TO_SQM_FACTOR = Decimal("100.00")


def sqft_to_sqm(sqft: Decimal) -> Decimal:
    """Converts Square Feet to Square Meters (rounded to 2 decimal places)."""
    return (sqft / SQM_TO_SQFT_FACTOR).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def sqm_to_sqft(sqm: Decimal) -> Decimal:
    """Converts Square Meters to Square Feet (rounded to 2 decimal places)."""
    return (sqm * SQM_TO_SQFT_FACTOR).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def guntha_to_sqft(guntha: Decimal) -> Decimal:
    """Converts Guntha to Square Feet."""
    return (guntha * GUNTHA_TO_SQFT_FACTOR).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def hectare_r_to_sqm(hectare: Decimal, r: Decimal) -> Decimal:
    """Converts Hectare-R notation (e.g. 1 Hectare 20 R) to Square Meters."""
    return (hectare * HECTARE_TO_SQM_FACTOR) + (r * ARE_TO_SQM_FACTOR)


def format_in_words_mr_area(sqm: Decimal, sqft: Decimal) -> str:
    """Formats area for Marathi deed clause."""
    return f"{sqm} चौ. मी. (समकक्ष {sqft} चौ. फूट)"
