"""English language pack for property legal drafting (Indian legal convention).

Implements:
- Indian numbering system in words (Crore, Lakh, Thousand, Hundred, Paise)
- Mathematical inverse parser (words_to_number_en) test oracle
- Indian number grouping currency formatter (e.g. Rs. 13,10,000/-)
- Statutory honorifics, dates, and name conjunctions
"""

from __future__ import annotations

import datetime
import re
from decimal import ROUND_HALF_UP, Decimal

EN_ONES: dict[int, str] = {
    0: "Zero",
    1: "One",
    2: "Two",
    3: "Three",
    4: "Four",
    5: "Five",
    6: "Six",
    7: "Seven",
    8: "Eight",
    9: "Nine",
    10: "Ten",
    11: "Eleven",
    12: "Twelve",
    13: "Thirteen",
    14: "Fourteen",
    15: "Fifteen",
    16: "Sixteen",
    17: "Seventeen",
    18: "Eighteen",
    19: "Nineteen",
}

EN_TENS: dict[int, str] = {
    20: "Twenty",
    30: "Thirty",
    40: "Forty",
    50: "Fifty",
    60: "Sixty",
    70: "Seventy",
    80: "Eighty",
    90: "Ninety",
}

# Reverse lookup dictionary for inverse parsing
EN_WORDS_TO_NUM: dict[str, int] = {v.lower(): k for k, v in EN_ONES.items()}
for k, v in EN_TENS.items():
    EN_WORDS_TO_NUM[v.lower()] = k


def _under_hundred_to_words_en(n: int) -> str:
    """Converts 0-99 to English words."""
    if n < 20:
        return EN_ONES[n]
    tens_val = (n // 10) * 10
    rem = n % 10
    if rem == 0:
        return EN_TENS[tens_val]
    return f"{EN_TENS[tens_val]} {EN_ONES[rem]}"


def number_to_words_en(amount: int | Decimal, *, currency: bool = True) -> str:
    """Converts a numerical amount into formal English words using Indian numbering.

    Example: 1550000 -> 'Rupees Fifteen Lakh Fifty Thousand Only'
    Example: 1250000.50 -> 'Rupees Twelve Lakh Fifty Thousand and Fifty Paise Only'
    """
    d_amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    integer_part = int(d_amount)
    paise_part = int((d_amount - integer_part) * 100)

    if integer_part == 0 and paise_part == 0:
        return "Rupees Zero Only" if currency else "Zero"

    parts: list[str] = []

    # Crores (1,00,00,000)
    crores = integer_part // 10_000_000
    integer_part %= 10_000_000
    if crores > 0:
        parts.append(f"{number_to_words_en(crores, currency=False)} Crore")

    # Lakhs (1,00,000)
    lakhs = integer_part // 100_000
    integer_part %= 100_000
    if lakhs > 0:
        parts.append(f"{_under_hundred_to_words_en(lakhs)} Lakh")

    # Thousands (1,000)
    thousands = integer_part // 1_000
    integer_part %= 1_000
    if thousands > 0:
        parts.append(f"{_under_hundred_to_words_en(thousands)} Thousand")

    # Hundreds (100)
    hundreds = integer_part // 100
    integer_part %= 100
    if hundreds > 0:
        parts.append(f"{EN_ONES[hundreds]} Hundred")

    # Remainder 0-99
    if integer_part > 0:
        parts.append(_under_hundred_to_words_en(integer_part))

    words = " ".join(parts) if parts else "Zero"

    if paise_part > 0:
        paise_words = _under_hundred_to_words_en(paise_part)
        if currency:
            return f"Rupees {words} and {paise_words} Paise Only"
        return f"{words} and {paise_words} Paise"

    if currency:
        return f"Rupees {words} Only"
    return words


def words_to_number_en(text: str) -> Decimal:
    """Mathematical inverse parser: converts English legal words back to exact Decimal.

    Handles Indian units (Crore, Lakh, Thousand, Hundred, Paise).
    """
    clean = text.lower()
    clean = re.sub(r"\b(rupees|rupee|only|and)\b", "", clean)
    clean = clean.strip()

    if not clean or clean == "zero":
        return Decimal("0.00")

    paise = 0
    if "paise" in clean:
        main_part, paise_part = (
            clean.split("paise", 1)[0].split("and", 1)
            if "and" in clean
            else (clean.replace("paise", ""), "0")
        )
        clean = main_part.strip()
        # Parse paise
        paise_words = [w for w in paise_part.replace("paise", "").strip().split() if w]
        paise = _parse_simple_phrase_en(paise_words)

    tokens = clean.split()
    total = 0
    current_chunk = 0

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in EN_WORDS_TO_NUM:
            current_chunk += EN_WORDS_TO_NUM[tok]
        elif tok == "hundred":
            current_chunk = max(1, current_chunk) * 100
        elif tok == "thousand":
            current_chunk = max(1, current_chunk) * 1_000
            total += current_chunk
            current_chunk = 0
        elif tok in ("lakh", "lacs"):
            current_chunk = max(1, current_chunk) * 100_000
            total += current_chunk
            current_chunk = 0
        elif tok in ("crore", "crores"):
            current_chunk = max(1, current_chunk) * 10_000_000
            total += current_chunk
            current_chunk = 0
        i += 1

    total += current_chunk
    result = Decimal(str(total))
    if paise > 0:
        result += Decimal(str(paise)) / Decimal("100")

    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _parse_simple_phrase_en(words: list[str]) -> int:
    val = 0
    for w in words:
        if w in EN_WORDS_TO_NUM:
            val += EN_WORDS_TO_NUM[w]
    return val


def format_currency_indian_en(amount: Decimal | int) -> str:
    """Formats monetary amount using Indian digit grouping (e.g. 13,10,000.00)."""
    d = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    int_str, _, dec_str = str(d).partition(".")

    is_negative = int_str.startswith("-")
    if is_negative:
        int_str = int_str[1:]

    if len(int_str) <= 3:
        formatted = int_str
    else:
        last3 = int_str[-3:]
        rest = int_str[:-3]
        groups: list[str] = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        formatted = ",".join(groups) + "," + last3

    if is_negative:
        formatted = "-" + formatted

    if dec_str and dec_str != "00":
        return f"Rs. {formatted}.{dec_str}/-"
    return f"Rs. {formatted}/-"


class EnglishLanguagePack:
    """English language pack conforming to LanguagePack protocol."""

    code = "en"
    name = "English (Indian Legal)"

    def number_to_words(self, n: Decimal | int, *, currency: bool = True) -> str:
        return number_to_words_en(n, currency=currency)

    def words_to_number(self, text: str) -> Decimal:
        return words_to_number_en(text)

    def format_date(self, d: datetime.date, style: str = "formal") -> str:
        # Ordinal suffix 1st, 2nd, 3rd, 4th...
        day = d.day
        suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return f"{day}{suffix} {d.strftime('%B %Y')}"

    def to_digits(self, s: str) -> str:
        return s

    def to_western_digits(self, s: str) -> str:
        return s

    def honorific(self, gender: str, marital_status: str | None = None) -> str:
        g = gender.strip().lower()
        if g == "male":
            return "Mr."
        if g == "female":
            if marital_status and marital_status.strip().lower() in ("unmarried", "single"):
                return "Ms."
            return "Mrs."
        return "Mr./Ms."

    def join_names(self, names: list[str]) -> str:
        if not names:
            return ""
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return f"{names[0]} and {names[1]}"
        return f"{', '.join(names[:-1])} and {names[-1]}"

    def plural(self, count: int) -> bool:
        return count > 1

    def format_currency(self, amount: Decimal | int) -> str:
        return format_currency_indian_en(amount)

    def format_area(self, area: Decimal, unit: str) -> str:
        unit_map = {
            "sqm": "Sq. Mtrs.",
            "sqft": "Sq. Ft.",
            "guntha": "Gunthas",
            "hectare": "Hectares",
        }
        unit_label = unit_map.get(unit.lower(), unit)
        return f"{area} {unit_label}"
