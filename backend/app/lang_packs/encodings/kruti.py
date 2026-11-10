"""Kruti Dev / DevLys to Unicode Devanagari converter.

Supports run-aware conversion, pre-base 'i' matra reordering, post-base reph,
conjunct mapping, Marathi-specific retroflex L ('ळ'), and Latin-in-Kruti detection.
All output text is normalized to NFC.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Sequence

# Known Kruti Dev / DevLys font family substrings
KRUTI_FONT_NAMES = (
    "kruti",
    "krutidev",
    "kruti dev",
    "devlys",
    "dev lys",
    "kdm",
    "chanakya",
)

# Multi-character conjuncts and complex replacements in Kruti Dev
MULTI_CHAR_MAP: list[tuple[str, str]] = [
    # Eyelash reph and Marathi special combinations
    ("Z;k", "ऱ्‍या"),
    ("Z;", "ऱ्‍य"),
    # Common conjuncts
    ("=k", "त्र"),
    ("{k", "क्ष"),
    ("K", "ज्ञ"),
    ("J", "श्र"),
    ("Í", "त्त"),
    ("Î", "क्त"),
    ("å", "द्व"),
    ("Æ", "द्य"),
    ("Ï", "द्द"),
    ("Ð", "द्ध"),
    ("Ñ", "कृ"),
    ("ñ", "हृ"),
    ("ò", "ह्न"),
    ("ó", "ह्म"),
    ("ô", "ह्य"),
    ("õ", "ह्र"),
    ("ö", "ह्ल"),
    ("÷", "ह्व"),
    ("ø", "ष्ट"),
    ("ù", "ष्ठ"),
    ("ú", "ङ्ग"),
    ("û", "ङ्क"),
    ("ü", "ङ्ख"),
    ("ý", "ङ्घ"),
    ("þ", "च्च"),
    # Full vowels with vowel signs
    ("vks", "ओ"),
    ("vkS", "औ"),
    ("vk", "आ"),
    ("bZ", "ई"),
    ("b", "इ"),
    ("m", "उ"),
    ("Å", "ऊ"),
    (",s", "ऐ"),
    (",", "ए"),
    ("v", "अ"),
    # Consonants with explicit 'k' forming full letter
    ("[k", "ख"),
    ("?k", "घ"),
    (".k", "ण"),
    ("Fk", "थ"),
    ("/k", "ध"),
    ("Hk", "भ"),
    ("'k", "श"),
    ('"k', "ष"),
]

# Single character / glyph direct mapping
SINGLE_CHAR_MAP: dict[str, str] = {
    # Full Consonants
    "d": "क",
    "x": "ग",
    "³": "ङ",
    "p": "च",
    "N": "छ",
    "t": "ज",
    "T": "झ",
    "¥": "ञ",
    "V": "ट",
    "B": "ठ",
    "M": "ड",
    "<": "ढ",
    "r": "त",
    "n": "द",
    "u": "न",
    "i": "प",
    "Q": "फ",
    "c": "ब",
    "e": "म",
    ";": "य",
    "j": "र",
    "y": "ल",
    "o": "व",
    "l": "स",
    "g": "ह",
    "G": "ळ",  # Marathi retroflex L
    # Half Consonants (carrying virama ्)
    "D": "क्",
    "[": "ख्",
    "X": "ग्",
    "?": "घ्",
    "P": "च्",
    "T": "ज्",
    ".": "ण्",
    "R": "त्",
    "F": "थ्",
    "/": "ध्",
    "U": "न्",
    "I": "प्",
    "C": "ब्",
    "H": "भ्",
    "E": "म्",
    "Y": "ल्",
    "O": "व्",
    "'": "श्",
    '"': "ष्",
    "L": "स्",
    # Matras (Vowel signs)
    "k": "ा",
    "h": "ी",
    "q": "ु",
    "w": "ू",
    "`": "ृ",
    "s": "े",
    "S": "ै",
    "a": "ं",  # Anusvara
    "%": "ः",  # Visarga
    "¡": "ँ",  # Chandrabindu
    "~": "्",  # Virama
    # Numerals (Default mapping preserves Western numerals or maps to Devanagari)
    "0": "०",
    "1": "१",
    "2": "२",
    "3": "३",
    "4": "४",
    "5": "५",
    "6": "६",
    "7": "७",
    "8": "८",
    "9": "९",
    # Punctuation
    "-": "-",
    "A": "।",  # Purna viram (Danda)
    "\\": "d",
}


@dataclass(frozen=True)
class LatinDetectionWarning:
    """Warning for suspected Latin text typed in a Kruti font run."""

    text: str
    pattern_type: str
    position: int


class KrutiConverter:
    """Production-grade Kruti Dev / DevLys to Unicode converter."""

    @staticmethod
    def is_kruti_font(font_name: str | None) -> bool:
        """Determines if the given font name belongs to the Kruti/DevLys family."""
        if not font_name:
            return False
        clean = font_name.strip().lower()
        return any(k in clean for k in KRUTI_FONT_NAMES)

    @staticmethod
    def detect_latin_in_kruti(raw_text: str) -> list[LatinDetectionWarning]:
        """Identifies patterns suggesting Latin text typed under a Kruti font."""
        warnings: list[LatinDetectionWarning] = []

        # PAN pattern: 5 uppercase letters, 4 digits, 1 uppercase letter
        for match in re.finditer(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", raw_text):
            warnings.append(
                LatinDetectionWarning(
                    text=match.group(0),
                    pattern_type="PAN",
                    position=match.start(),
                )
            )

        # 10 to 12 digit numbers (Phone or Aadhaar-like)
        for match in re.finditer(r"\b\d{10,12}\b", raw_text):
            warnings.append(
                LatinDetectionWarning(
                    text=match.group(0),
                    pattern_type="10_12_DIGIT_ID",
                    position=match.start(),
                )
            )

        # Common Latin words typed by mistake
        for match in re.finditer(
            r"\b(NIT|NMC|CITY|SURVEY|PLOT|MOUZA|KHASRA|GAT|FLAT|SHOP|CHEQUE|BANK|IFSC)\b",
            raw_text,
            re.IGNORECASE,
        ):
            warnings.append(
                LatinDetectionWarning(
                    text=match.group(0),
                    pattern_type="LATIN_KEYWORD",
                    position=match.start(),
                )
            )

        return warnings

    @classmethod
    def convert_string(cls, raw: str) -> str:
        """Converts a Kruti Dev encoded string to Unicode Devanagari."""
        if not raw:
            return ""

        # Step 1: Pre-process pre-base short 'i' matra ('f')
        # In Kruti Dev, 'f' precedes the consonant cluster.
        # e.g., 'fd' -> 'df' (which maps to क + ि = कि)
        # e.g., 'fD;' -> 'D;f' (which maps to क् + य + ि = क्यि)
        # e.g., 'fLFk' -> 'LFkf' (which maps to स् + थ + ि = स्थि)
        text = cls._reorder_pre_base_i(raw)

        # Step 2: Pre-process post-base reph ('Z')
        # In Kruti Dev, 'Z' follows the character it sits on.
        # e.g., 'dZ' -> 'Zd' (which maps to र् + क = र्क)
        # e.g., 'dkZ' -> 'Zdk' (which maps to र् + का = र्का)
        text = cls._reorder_reph(text)

        # Step 3: Replace multi-character sequences
        for kruti_seq, unicode_seq in MULTI_CHAR_MAP:
            text = text.replace(kruti_seq, unicode_seq)

        # Step 4: Map single characters
        out_chars: list[str] = []
        for ch in text:
            if ch in SINGLE_CHAR_MAP:
                out_chars.append(SINGLE_CHAR_MAP[ch])
            elif ch == "f":
                out_chars.append("ि")
            elif ch == "Z":
                out_chars.append("र्")
            else:
                out_chars.append(ch)

        result = "".join(out_chars)

        # Step 5: Post-processing fixes (clean up virama combinations, matras)
        # If 'र्' followed by matra, ensure 'र्' precedes the base consonant
        result = cls._normalize_reph_placement(result)

        # Step 6: NFC Unicode normalization
        return unicodedata.normalize("NFC", result)

    @classmethod
    def to_kruti(cls, unicode_text: str) -> str:
        """Converts Unicode Devanagari text back to Kruti Dev glyph string.

        Used for round-trip regression testing and optional legacy export.
        """
        if not unicode_text:
            return ""

        text = unicodedata.normalize("NFC", unicode_text)

        # Reverse multi-char mappings (sorted by length of Unicode sequence descending)
        rev_multi = sorted(
            [(u, k) for k, u in MULTI_CHAR_MAP],
            key=lambda item: len(item[0]),
            reverse=True,
        )
        for u_seq, k_seq in rev_multi:
            text = text.replace(u_seq, k_seq)

        # Reverse single char mappings
        rev_single = {u: k for k, u in SINGLE_CHAR_MAP.items()}
        chars: list[str] = []
        for ch in text:
            if ch in rev_single:
                chars.append(rev_single[ch])
            elif ch == "ि":
                chars.append("f")
            elif ch == "्":
                chars.append("~")
            else:
                chars.append(ch)

        res = "".join(chars)

        # Post-process: restore Kruti 'f' (pre-base i-matra before consonant)
        # e.g., 'df' -> 'fd'
        res = re.sub(r"([a-zA-Z~])f", r"f\1", res)

        return res

    @classmethod
    def compute_roundtrip_score(cls, kruti_text: str) -> tuple[float, str, list[str]]:
        """Computes round-trip conversion fidelity score (%) and flags anomalies.

        Formula: SequenceMatcher(kruti_original, kruti_roundtrip).ratio() * 100.0
        """
        import difflib

        if not kruti_text or kruti_text.strip() == "":
            return 100.0, "", []

        unicode_str = cls.convert_string(kruti_text)
        kruti_roundtrip = cls.to_kruti(unicode_str)

        matcher = difflib.SequenceMatcher(None, kruti_text, kruti_roundtrip)
        score = round(matcher.ratio() * 100.0, 2)

        anomalies: list[str] = []
        if score < 98.0:
            for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
                if opcode != "equal":
                    anomalies.append(
                        f"Diff [{opcode}]: original '{kruti_text[a0:a1]}' vs reconstructed '{kruti_roundtrip[b0:b1]}'"
                    )

        return score, kruti_roundtrip, anomalies

    @staticmethod
    def _reorder_pre_base_i(text: str) -> str:
        """Moves 'f' (short i matra) after the following consonant cluster."""
        chars = list(text)
        length = len(chars)
        i = 0
        while i < length:
            if chars[i] == "f" and i + 1 < length:
                # Find the end of the consonant cluster following 'f'
                # In Kruti, half consonants are capital letters like D, X, P, L, F, etc.
                # Consonant with 'k' may be two characters like [k, ?k, Fk, /k, Hk, 'k, "k.
                j = i + 1
                while j < length and chars[j] in "DXP.RFIHCHEEYO'\"L[/?":
                    j += 1
                if j < length:
                    # Check for two-character consonants like [k, ?k, etc.
                    if j + 1 < length and chars[j + 1] == "k" and chars[j] in "[?.F/'\"H":
                        j += 1
                    # Swap 'f' to after the base consonant
                    f_char = chars.pop(i)
                    chars.insert(j, f_char)
                    i = j
            i += 1
        return "".join(chars)

    @staticmethod
    def _reorder_reph(text: str) -> str:
        """Moves 'Z' (reph) to before the preceding consonant cluster."""
        chars = list(text)
        i = 0
        while i < len(chars):
            if chars[i] == "Z" and i > 0:
                # Find the beginning of the base consonant cluster preceding 'Z'
                j = i - 1
                # Skip matras attached to base consonant (k, h, q, w, s, S, a, %)
                while j >= 0 and chars[j] in "khqwsSa%":
                    j -= 1
                # Skip the base consonant
                if j >= 0:
                    # If preceded by two-char consonant (e.g. [k, Fk, 'k), skip back one more
                    if j > 0 and chars[j] == "k" and chars[j - 1] in "[?.F/'\"H":
                        j -= 1
                # Skip preceding half consonants
                while j > 0 and chars[j - 1] in "DXP.RFIHCHEEYO'\"L[/?":
                    j -= 1
                if j >= 0 and j < i:
                    z_char = chars.pop(i)
                    chars.insert(j, z_char)
            i += 1
        return "".join(chars)

    @staticmethod
    def _normalize_reph_placement(text: str) -> str:
        """Fixes reph placement if virama or matras were displaced."""
        # e.g., 'ा' + 'र्' -> 'र्' + 'ा'
        text = re.sub(r"([ाीुूेैोौूंः])र्", r"र्\1", text)
        return text


@dataclass
class RunSegment:
    """Segment of text from a run with its formatting metadata."""

    text: str
    font_name: str | None
    bold: bool | None
    italic: bool | None
    size_pt: float | None
    is_kruti: bool


def merge_adjacent_runs(runs: Sequence[RunSegment]) -> list[RunSegment]:
    """Merges adjacent runs that share the identical font, bold, and italic attributes.

    Prevents matra and conjunct breaks across split run boundaries.
    """
    if not runs:
        return []

    merged: list[RunSegment] = []
    current = RunSegment(
        text=runs[0].text,
        font_name=runs[0].font_name,
        bold=runs[0].bold,
        italic=runs[0].italic,
        size_pt=runs[0].size_pt,
        is_kruti=runs[0].is_kruti,
    )

    for run in runs[1:]:
        can_merge = (
            run.font_name == current.font_name
            and run.bold == current.bold
            and run.italic == current.italic
            and run.is_kruti == current.is_kruti
        )
        if can_merge:
            current.text += run.text
        else:
            merged.append(current)
            current = RunSegment(
                text=run.text,
                font_name=run.font_name,
                bold=run.bold,
                italic=run.italic,
                size_pt=run.size_pt,
                is_kruti=run.is_kruti,
            )

    merged.append(current)
    return merged

