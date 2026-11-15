"""Golden vector tests for formal legal Marathi amount in words (PRD FR-08, Features F-003).

Validates conformance against the shared golden vector file `conformance/marathi_numbers.json`.
Verified vectors must match `number_to_words_mr` output exactly.
Rows awaiting legal review are flagged as `TODO(lawyer)`.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from app.lang_packs.marathi import number_to_words_mr

GOLDEN_VECTORS_PATH = (
    Path(__file__).parent.parent.parent.parent / "conformance" / "marathi_numbers.json"
)


def _load_golden_vectors() -> list[dict[str, Any]]:
    """Loads golden vectors from conformance file."""
    assert GOLDEN_VECTORS_PATH.exists(), f"Golden vectors file missing at {GOLDEN_VECTORS_PATH}"
    with open(GOLDEN_VECTORS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.golden
def test_marathi_numbers_golden_vectors() -> None:
    """Verifies that number_to_words_mr matches approved Marathi legal words."""
    vectors = _load_golden_vectors()
    assert len(vectors) > 0, "No golden vectors found"

    for vec in vectors:
        amount_dec = Decimal(vec["amount"])
        expected_words = vec["words"]
        is_verified = vec.get("verified", False)
        notes = vec.get("notes", "")

        if not is_verified:
            # Unverified rows are designated for lawyer signoff
            assert "TODO(lawyer)" in notes, (
                f"Unverified row for {vec['amount']} must be marked TODO(lawyer)"
            )
            continue

        actual_words = number_to_words_mr(amount_dec, currency=True)
        assert actual_words == expected_words, (
            f"Marathi words mismatch for amount {vec['amount']}:\n"
            f"  Expected: {expected_words}\n"
            f"  Actual:   {actual_words}\n"
            f"  Notes:    {notes}"
        )
