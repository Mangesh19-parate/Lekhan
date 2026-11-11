"""Document comparison and grapheme-aware legal text diff engine (Features F-030, F-066).

Strict compliance with AGENTS.md:
- Devanagari text normalized to NFC.
- Compares legal clauses at paragraph and word levels without slicing code points mid-grapheme.
- Produces clean addition, deletion, and unchanged hunks for advocates and template reviewers.
"""

from __future__ import annotations

import difflib
import unicodedata
from dataclasses import asdict, dataclass
from typing import Literal


@dataclass
class DiffHunk:
    tag: Literal["equal", "insert", "delete", "replace"]
    a_text: str
    b_text: str
    a_start: int
    a_end: int
    b_start: int
    b_end: int


@dataclass
class DocumentComparisonResult:
    similarity_ratio: float
    total_additions: int
    total_deletions: int
    hunks: list[DiffHunk]


def normalize_legal_text(text: str) -> str:
    """Normalizes text to Unicode NFC and regularizes paragraph breaks."""
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").strip())


def diff_legal_texts(
    text_a: str,
    text_b: str,
    granularity: Literal["paragraph", "word", "line"] = "word",
) -> DocumentComparisonResult:
    """Computes grapheme-aware legal diff between two document or template texts (Features F-030, F-066)."""
    norm_a = normalize_legal_text(text_a)
    norm_b = normalize_legal_text(text_b)

    if granularity == "paragraph":
        tokens_a = [p for p in norm_a.split("\n\n") if p]
        tokens_b = [p for p in norm_b.split("\n\n") if p]
        joiner = "\n\n"
    elif granularity == "line":
        tokens_a = norm_a.splitlines()
        tokens_b = norm_b.splitlines()
        joiner = "\n"
    else:  # word level
        tokens_a = norm_a.split()
        tokens_b = norm_b.split()
        joiner = " "

    matcher = difflib.SequenceMatcher(None, tokens_a, tokens_b)
    hunks: list[DiffHunk] = []
    total_additions = 0
    total_deletions = 0

    for tag, alo, ahi, blo, bhi in matcher.get_opcodes():
        sub_a = joiner.join(tokens_a[alo:ahi])
        sub_b = joiner.join(tokens_b[blo:bhi])

        if tag == "insert":
            total_additions += len(tokens_b[blo:bhi])
        elif tag == "delete":
            total_deletions += len(tokens_a[alo:ahi])
        elif tag == "replace":
            total_deletions += len(tokens_a[alo:ahi])
            total_additions += len(tokens_b[blo:bhi])

        hunks.append(
            DiffHunk(
                tag=tag,  # type: ignore[arg-type]
                a_text=sub_a,
                b_text=sub_b,
                a_start=alo,
                a_end=ahi,
                b_start=blo,
                b_end=bhi,
            )
        )

    return DocumentComparisonResult(
        similarity_ratio=round(matcher.ratio(), 4),
        total_additions=total_additions,
        total_deletions=total_deletions,
        hunks=hunks,
    )
