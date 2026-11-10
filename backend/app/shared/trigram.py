"""Devanagari and Multilingual Trigram Search Engine (PRD FR-14, Features F-061).

Implements PostgreSQL pg_trgm-compatible trigram generation and similarity calculation:
- Unicode NFC normalization per AGENTS.md Domain Rules.
- Padded 3-gram extraction.
- Jaccard similarity index S = |A ∩ B| / |A ∪ B|.
- Substring match boost for prefix/infix queries.
"""

from __future__ import annotations

import unicodedata
from typing import Set


def normalize_text(text: str) -> str:
    """Normalizes text to Unicode NFC and lowercases for consistent matching."""
    if not text:
        return ""
    nfc_text = unicodedata.normalize("NFC", text.strip())
    return nfc_text.lower()


def generate_trigrams(text: str) -> Set[str]:
    """Generates 3-character shingles following pg_trgm padding rules.

    Standard pg_trgm prepends two spaces and appends one space to capture boundary trigrams.
    Example: "राम" -> "  राम " -> trigrams: {"  र", " रा", "राम", "ाम "}
    """
    clean = normalize_text(text)
    if not clean:
        return set()

    # Prepend 2 spaces and append 1 space per pg_trgm convention
    padded = f"  {clean} "
    trigrams: set[str] = set()
    for i in range(len(padded) - 2):
        trigrams.add(padded[i : i + 3])
    return trigrams


def trigram_similarity(query: str, target: str) -> float:
    """Computes trigram similarity between query and target string [0.0 - 1.0]."""
    q_norm = normalize_text(query)
    t_norm = normalize_text(target)

    if not q_norm or not t_norm:
        return 0.0

    # Exact match shortcut
    if q_norm == t_norm:
        return 1.0

    # Direct substring shortcut boost
    substring_boost = 0.0
    if q_norm in t_norm:
        substring_boost = 0.35 * (len(q_norm) / len(t_norm))

    q_tri = generate_trigrams(q_norm)
    t_tri = generate_trigrams(t_norm)

    if not q_tri or not t_tri:
        return 0.0

    intersection_len = len(q_tri & t_tri)
    union_len = len(q_tri | t_tri)

    if union_len == 0:
        return 0.0

    base_similarity = intersection_len / union_len
    return min(1.0, base_similarity + substring_boost)

