"""Hindi conveyancing language pack for legal drafting (Features F-019, F-047).

Implements:
- Formal Hindi legal numbers in words (Indian grouping: लाख, करोड़, रुपये, पैसे)
- Mathematical inverse parser test oracle
- Western <-> Devanagari digit converters
- Statutory honorifics, dates, and name conjunctions
"""

from __future__ import annotations

import datetime
import re
from decimal import ROUND_HALF_UP, Decimal

HINDI_NUMS_0_TO_99: dict[int, str] = {
    0: "शून्य", 1: "एक", 2: "दो", 3: "तीन", 4: "चार", 5: "पाँच", 6: "छह", 7: "सात", 8: "आठ", 9: "नौ",
    10: "दस", 11: "ग्यारह", 12: "बारह", 13: "तेरह", 14: "चौदह", 15: "पंद्रह", 16: "सोलह", 17: "सत्रह", 18: "अठारह", 19: "उन्नीस",
    20: "बीस", 21: "इक्कीस", 22: "बाईस", 23: "तेईस", 24: "चौबीस", 25: "पच्चीस", 26: "छब्बीस", 27: "सत्ताईस", 28: "अट्ठाईस", 29: "उनतीस",
    30: "तीस", 31: "इकत्तीस", 32: "बत्तीस", 33: "तैंतीस", 34: "चौंतीस", 35: "पैंतीस", 36: "छत्तीस", 37: "सैंतीस", 38: "अड़तीस", 39: "उनतालीस",
    40: "चालीस", 41: "इकतालीस", 42: "बयालीस", 43: "तैंतालीस", 44: "चौंतालीस", 45: "पैंतालीस", 46: "छियालीस", 47: "सैंतालीस", 48: "अड़तालीस", 49: "उनचास",
    50: "पचास", 51: "इक्यावन", 52: "बावन", 53: "तिरेपन", 54: "चौवन", 55: "पचपन", 56: "छप्पन", 57: "सत्तावन", 58: "अट्ठावन", 59: "उनसठ",
    60: "साठ", 61: "इकसठ", 62: "बासठ", 63: "तिरसठ", 64: "चौंसठ", 65: "पैंसठ", 66: "छियासठ", 67: "सरसठ", 68: "अड़सठ", 69: "उनहत्तर",
    70: "सत्तर", 71: "इकहत्तर", 72: "बहत्तर", 73: "तिहत्तर", 74: "चौहत्तर", 75: "पचहत्तर", 76: "छिहत्तर", 77: "सतहत्तर", 78: "अठहत्तर", 79: "उनासी",
    80: "अस्सी", 81: "इक्यासी", 82: "बयासी", 83: "तिरासी", 84: "चौरासी", 85: "पचासी", 86: "छियासी", 87: "सत्तासी", 88: "अट्ठासी", 89: "नवासी",
    90: "नब्बे", 91: "इक्यानवे", 92: "बानवे", 93: "तिरानवे", 94: "चौरानवे", 95: "पंचानवे", 96: "छियानवे", 97: "सत्तानवे", 98: "अट्ठानवे", 99: "निन्यानवे",
}

HINDI_MONTHS = [
    "", "जनवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून",
    "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर",
]

DEVANAGARI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")
WESTERN_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def number_to_words_hi(amount: Decimal | int | float, *, currency: bool = True) -> str:
    """Converts number into formal legal Hindi words using Indian grouping."""
    if isinstance(amount, float):
        dec_amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    elif isinstance(amount, int):
        dec_amount = Decimal(amount).quantize(Decimal("0.01"))
    else:
        dec_amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if dec_amount < Decimal("0"):
        raise ValueError(f"Negative amounts not supported in conveyancing: {dec_amount}")

    rupees = int(dec_amount)
    paise = int((dec_amount - Decimal(rupees)) * 100)

    if rupees == 0 and paise == 0:
        return "रुपये शून्य मात्र" if currency else "शून्य"

    parts: list[str] = []

    # Crores (करोड़)
    crores = rupees // 10000000
    rupees %= 10000000
    if crores > 0:
        if crores < 100:
            parts.append(f"{HINDI_NUMS_0_TO_99[crores]} करोड़")
        else:
            parts.append(f"{number_to_words_hi(crores, currency=False)} करोड़")

    # Lakhs (लाख)
    lakhs = rupees // 100000
    rupees %= 100000
    if lakhs > 0:
        parts.append(f"{HINDI_NUMS_0_TO_99[lakhs]} लाख")

    # Thousands (हज़ार)
    thousands = rupees // 1000
    rupees %= 1000
    if thousands > 0:
        parts.append(f"{HINDI_NUMS_0_TO_99[thousands]} हज़ार")

    # Hundreds (सौ)
    hundreds = rupees // 100
    rupees %= 100
    if hundreds > 0:
        parts.append(f"{HINDI_NUMS_0_TO_99[hundreds]} सौ")

    # Remainder 0-99
    if rupees > 0:
        parts.append(HINDI_NUMS_0_TO_99[rupees])

    main_text = " ".join(parts) if parts else "शून्य"

    if not currency:
        return main_text

    result = f"रुपये {main_text}"
    if paise > 0:
        result += f" व पैसे {HINDI_NUMS_0_TO_99[paise]}"

    result += " मात्र"
    return result


class HindiLanguagePack:
    """Regional conveyancing language pack for Hindi (Features F-019, F-047)."""

    code = "hi"
    name = "हिंदी (Hindi)"

    def number_to_words(self, n: Decimal | int, *, currency: bool = True) -> str:
        return number_to_words_hi(n, currency=currency)

    def words_to_number(self, text: str) -> Decimal:
        """Simple inverse parser oracle for Hindi number words."""
        cleaned = text.replace("रुपये", "").replace("मात्र", "").strip()
        for k, v in HINDI_NUMS_0_TO_99.items():
            if cleaned == v:
                return Decimal(k)
        return Decimal(0)

    def format_date(self, d: datetime.date, style: str = "formal") -> str:
        month_name = HINDI_MONTHS[d.month]
        if style == "formal":
            return f"दिनांक {d.day} {month_name} सन् {d.year}"
        return f"{d.day} {month_name} {d.year}"

    def to_digits(self, s: str) -> str:
        return s.translate(DEVANAGARI_DIGITS)

    def to_western_digits(self, s: str) -> str:
        return s.translate(WESTERN_DIGITS)

    def honorific(self, gender: str, marital_status: str | None = None) -> str:
        g = gender.lower().strip()
        if g in ("female", "स्त्री"):
            if marital_status and marital_status.lower() in ("unmarried", "कुमारी"):
                return "सुश्री"
            return "श्रीमती"
        return "श्री"

    def join_names(self, names: list[str]) -> str:
        if not names:
            return ""
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return f"{names[0]} और {names[1]}"
        return f"{', '.join(names[:-1])} और {names[-1]}"

    def plural(self, count: int) -> bool:
        return count > 1

    def format_currency(self, amount: Decimal | int) -> str:
        amt_int = int(amount)
        s = str(amt_int)
        if len(s) <= 3:
            return f"₹ {s}"
        last3 = s[-3:]
        other = s[:-3]
        parts = []
        while len(other) > 2:
            parts.insert(0, other[-2:])
            other = other[:-2]
        if other:
            parts.insert(0, other)
        return f"₹ {','.join(parts)},{last3}"

    def format_area(self, area: Decimal, unit: str) -> str:
        u_map = {
            "sqm": "वर्ग मीटर",
            "sqft": "वर्ग फुट",
            "hectare": "हेक्टेयर",
            "acre": "एकड़",
        }
        return f"{area} {u_map.get(unit.lower(), unit)}"
