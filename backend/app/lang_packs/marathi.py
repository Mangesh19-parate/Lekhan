"""Marathi language pack for property legal drafting.

Implements:
- Formal Marathi legal numbers in words (0-99 table, लाख, कोटी, पैसे)
- Mathematical inverse parser (words_to_number_mr) test oracle
- Western <-> Devanagari digit converters (to_digits, to_western_digits)
- Indian number grouping currency formatter
- Statutory honorifics, dates, and name conjunctions
"""

from __future__ import annotations

import datetime
import re
from decimal import ROUND_HALF_UP, Decimal

# Marathi words for numbers 0 to 99
MARATHI_NUMS_0_TO_99: dict[int, str] = {
    0: "शून्य",
    1: "एक",
    2: "दोन",
    3: "तीन",
    4: "चार",
    5: "पाच",
    6: "सहा",
    7: "सात",
    8: "आठ",
    9: "नऊ",
    10: "दहा",
    11: "अकरा",
    12: "बारा",
    13: "तेरा",
    14: "चौदा",
    15: "पंधरा",
    16: "सोळा",
    17: "सतरा",
    18: "अठरा",
    19: "एकोणीस",
    20: "वीस",
    21: "एकवीस",
    22: "बावीस",
    23: "तेवीस",
    24: "चोवीस",
    25: "पंचवीस",
    26: "सव्वीस",
    27: "सत्तावीस",
    28: "अठ्ठावीस",
    29: "एकोणतीस",
    30: "तीस",
    31: "एकतीस",
    32: "बत्तीस",
    33: "तेहतीस",
    34: "चौतीस",
    35: "पस्तीस",
    36: "छत्तीस",
    37: "सदतीस",
    38: "अडतीस",
    39: "एकेचाळीस",
    40: "चाळीस",
    41: "एक्केचाळीस",
    42: "बेचाळीस",
    43: "त्रेचाळीस",
    44: "चव्वेचाळीस",
    45: "पंचेचाळीस",
    46: "शेहेचाळीस",
    47: "सत्तेचाळीस",
    48: "अठ्ठेचाळीस",
    49: "एकोणपन्नास",
    50: "पन्नास",
    51: "एक्कावन्न",
    52: "बावन्न",
    53: "त्रेपन्न",
    54: "चोपन्न",
    55: "पंचावन्न",
    56: "छप्पन्न",
    57: "सत्तावन्न",
    58: "अठ्ठावन्न",
    59: "एकोणसाठ",
    60: "साठ",
    61: "एकसष्ठ",
    62: "बासष्ठ",
    63: "त्रेसष्ठ",
    64: "चौसष्ठ",
    65: "पासष्ठ",
    66: "सहासष्ठ",
    67: "सदुसष्ठ",
    68: "अडुसष्ठ",
    69: "एकोणसत्तर",
    70: "सत्तर",
    71: "एकाहत्तर",
    72: "बाहत्तर",
    73: "त्र्याहत्तर",
    74: "चौहत्तर",
    75: "पंच्याहत्तर",
    76: "शहात्तर",
    77: "सत्त्याहत्तर",
    78: "अठ्ठ्याहत्तर",
    79: "एकोणऐंशी",
    80: "ऐंशी",
    81: "एक्याऐंशी",
    82: "ब्याऐंशी",
    83: "त्र्याऐंशी",
    84: "चौऱ्याऐंशी",
    85: "पंच्याऐंशी",
    86: "शहाऐंशी",
    87: "सत्त्याऐंशी",
    88: "अठ्ठाऐंशी",
    89: "एकोणनव्वद",
    90: "नव्वद",
    91: "एक्याण्णव",
    92: "ब्याण्णव",
    93: "त्र्याण्णव",
    94: "चौऱ्याण्णव",
    95: "पंच्याण्णव",
    96: "शहाण्णव",
    97: "सत्त्याण्णव",
    98: "अठ्ठ्याण्णव",
    99: "नव्व्याण्णव",
}

# Reverse lookup for inverse parsing
MARATHI_WORDS_TO_NUM: dict[str, int] = {v: k for k, v in MARATHI_NUMS_0_TO_99.items()}

# Devanagari digit mappings
LATIN_TO_DEVA = str.maketrans("0123456789", "०१२३४५६७८९")
DEVA_TO_LATIN = str.maketrans("०१२३४५६७८९", "0123456789")

MARATHI_MONTHS: dict[int, str] = {
    1: "जानेवारी",
    2: "फेब्रुवारी",
    3: "मार्च",
    4: "एप्रिल",
    5: "मे",
    6: "जून",
    7: "जुलै",
    8: "ऑगस्ट",
    9: "सप्टेंबर",
    10: "ऑक्टोबर",
    11: "नोव्हेंबर",
    12: "डिसेंबर",
}


def to_devanagari_digits(s: str) -> str:
    """Converts Latin digits 0-9 to Devanagari script digits ०-९."""
    return str(s).translate(LATIN_TO_DEVA)


def to_western_digits(s: str) -> str:
    """Converts Devanagari script digits ०-९ to standard Western digits 0-9."""
    return str(s).translate(DEVA_TO_LATIN)


def number_to_words_mr(amount: int | Decimal, *, currency: bool = True) -> str:
    """Converts an integer or Decimal into formal legal Marathi words.

    Example: 1550000 -> 'पंधरा लाख पन्नास हजार रुपये फक्त'
    Example: 1250000.50 -> 'बारा लाख पन्नास हजार रुपये आणि पन्नास पैसे फक्त'
    """
    d_amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    integer_part = int(d_amount)
    paise_part = int((d_amount - integer_part) * 100)

    if integer_part == 0 and paise_part == 0:
        return "शून्य रुपये फक्त" if currency else "शून्य"

    parts: list[str] = []

    # Crores (कोटी) - 1,00,00,000
    crores = integer_part // 10_000_000
    integer_part %= 10_000_000
    if crores > 0:
        parts.append(f"{_two_digit_to_words_mr(crores)} कोटी")

    # Lakhs (लाख) - 1,00,000
    lakhs = integer_part // 100_000
    integer_part %= 100_000
    if lakhs > 0:
        parts.append(f"{_two_digit_to_words_mr(lakhs)} लाख")

    # Thousands (हजार) - 1,000
    thousands = integer_part // 1_000
    integer_part %= 1_000
    if thousands > 0:
        parts.append(f"{_two_digit_to_words_mr(thousands)} हजार")

    # Hundreds (शे / शंभर) - 100
    hundreds = integer_part // 100
    integer_part %= 100
    if hundreds > 0:
        if hundreds == 1 and integer_part == 0:
            parts.append("शंभर")
        elif hundreds == 1:
            parts.append("एकशे")
        else:
            parts.append(f"{MARATHI_NUMS_0_TO_99[hundreds]}शे")

    # Remainder 0-99
    if integer_part > 0:
        parts.append(MARATHI_NUMS_0_TO_99[integer_part])

    words = " ".join(parts) if parts else "शून्य"

    if paise_part > 0:
        paise_words = MARATHI_NUMS_0_TO_99.get(paise_part, str(paise_part))
        if currency:
            return f"{words} रुपये आणि {paise_words} पैसे फक्त"
        return f"{words} आणि {paise_words} पैसे"

    if currency:
        return f"{words} रुपये फक्त"
    return words


def _two_digit_to_words_mr(val: int) -> str:
    """Helper for numbers 1 to 99."""
    if val in MARATHI_NUMS_0_TO_99:
        return MARATHI_NUMS_0_TO_99[val]
    return number_to_words_mr(val, currency=False)


def words_to_number_mr(text: str) -> Decimal:
    """Mathematical inverse parser: parses legal Marathi words back to exact Decimal.

    Handles कोटी, लाख, हजार, शे/शंभर, 0-99 and पैसे.
    """
    clean = text.strip()
    clean = re.sub(r"\b(रुपये|फक्त)\b", "", clean)
    clean = clean.strip()

    if not clean or clean == "शून्य":
        return Decimal("0.00")

    paise = 0
    if "पैसे" in clean:
        parts = clean.split("पैसे")[0].split("आणि")
        main_part = parts[0].strip()
        paise_word = parts[1].strip() if len(parts) > 1 else ""
        if paise_word in MARATHI_WORDS_TO_NUM:
            paise = MARATHI_WORDS_TO_NUM[paise_word]
        clean = main_part

    clean = re.sub(r"\bआणि\b", "", clean).strip()

    tokens = clean.split()
    total = 0
    current_chunk = 0

    i = 0
    while i < len(tokens):
        tok = tokens[i]

        # Check hundred forms like 'एकशे', 'दोनशे', 'पाचशे', 'शंभर'
        if tok == "शंभर":
            current_chunk += 100
        elif tok.endswith("शे"):
            prefix = tok[:-2]
            multiplier = MARATHI_WORDS_TO_NUM.get(prefix, 1)
            current_chunk += multiplier * 100
        elif tok in MARATHI_WORDS_TO_NUM:
            current_chunk += MARATHI_WORDS_TO_NUM[tok]
        elif tok == "हजार":
            current_chunk = max(1, current_chunk) * 1_000
            total += current_chunk
            current_chunk = 0
        elif tok == "लाख":
            current_chunk = max(1, current_chunk) * 100_000
            total += current_chunk
            current_chunk = 0
        elif tok == "कोटी":
            current_chunk = max(1, current_chunk) * 10_000_000
            total += current_chunk
            current_chunk = 0

        i += 1

    total += current_chunk
    result = Decimal(str(total))
    if paise > 0:
        result += Decimal(str(paise)) / Decimal("100")

    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_currency_indian_mr(amount: Decimal | int, *, devanagari: bool = False) -> str:
    """Formats currency in Indian number grouping with Marathi prefix."""
    from app.lang_packs.english import format_currency_indian_en

    # Leverage standard grouping logic
    en_fmt = format_currency_indian_en(amount)
    raw_num = en_fmt.replace("Rs. ", "").replace("/-", "")

    if devanagari:
        raw_num = to_devanagari_digits(raw_num)
    return f"रु. {raw_num}/-"


def format_date_mr(d: datetime.date, *, devanagari: bool = False) -> str:
    """Formats date in standard Marathi legal form: '०९ नोव्हेंबर २०२६'."""
    month_name = MARATHI_MONTHS.get(d.month, "")
    day_str = str(d.day)
    year_str = str(d.year)
    if devanagari:
        day_str = to_devanagari_digits(day_str)
        year_str = to_devanagari_digits(year_str)
    return f"{day_str} {month_name} {year_str}"


def get_honorific_mr(gender: str, marital_status: str | None = None) -> str:
    """Returns statutory Marathi honorific based on gender and status."""
    g = gender.strip().lower()
    if g == "male":
        return "श्री."
    if g == "female":
        if marital_status and marital_status.strip().lower() in ("unmarried", "single"):
            return "कु."
        return "सौ."
    return "श्री./सौ."


def join_party_names_mr(names: list[str]) -> str:
    """Joins multiple party names in Marathi style: 'A, B आणि C' or 'A व B'."""
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} व {names[1]}"
    return f"{', '.join(names[:-1])} व {names[-1]}"


class MarathiLanguagePack:
    """Marathi language pack conforming to LanguagePack protocol."""

    code = "mr"
    name = "मराठी (Marathi Legal)"

    def number_to_words(self, n: Decimal | int, *, currency: bool = True) -> str:
        return number_to_words_mr(n, currency=currency)

    def words_to_number(self, text: str) -> Decimal:
        return words_to_number_mr(text)

    def format_date(self, d: datetime.date, style: str = "formal") -> str:
        return format_date_mr(d, devanagari=False)

    def to_digits(self, s: str) -> str:
        return to_devanagari_digits(s)

    def to_western_digits(self, s: str) -> str:
        return to_western_digits(s)

    def honorific(self, gender: str, marital_status: str | None = None) -> str:
        return get_honorific_mr(gender, marital_status)

    def join_names(self, names: list[str]) -> str:
        return join_party_names_mr(names)

    def plural(self, count: int) -> bool:
        return count > 1

    def format_currency(self, amount: Decimal | int) -> str:
        return format_currency_indian_mr(amount, devanagari=False)

    def format_area(self, area: Decimal, unit: str) -> str:
        unit_map = {
            "sqm": "चौ.मी.",
            "sqft": "चौ.फूट",
            "guntha": "गुंठे",
            "hectare": "हेक्टर",
        }
        unit_label = unit_map.get(unit.lower(), unit)
        return f"{area} {unit_label}"
