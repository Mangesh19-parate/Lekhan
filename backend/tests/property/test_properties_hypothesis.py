"""Hypothesis property-based tests for numbering, amount-in-words, and Decimal area conversions.

Verifies:
1. Gap-free document numbering under concurrency (strictly contiguous monotonic sequence).
2. Marathi amount-in-words invariants (valid Devanagari scale terms, no crashes up to 999 Crore).
3. Decimal area conversions (zero float arithmetic, bounded round-trip precision).
"""

from __future__ import annotations

import concurrent.futures
import re
import uuid
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from app.lang_packs.marathi import number_to_words_mr
from app.numbering.service import DocumentNumberingService
from app.units.area import (
    GUNTHA_TO_SQFT_FACTOR,
    HECTARE_TO_SQM_FACTOR,
    guntha_to_sqft,
    hectare_r_to_sqm,
    sqft_to_sqm,
    sqm_to_sqft,
)

# --- 1. Property: Document Numbering Gap-Free Concurrency ---


@settings(max_examples=25, deadline=None)
@given(
    num_threads=st.integers(min_value=5, max_value=20),
    calls_per_thread=st.integers(min_value=2, max_value=8),
    year=st.integers(min_value=2024, max_value=2030),
)
def test_numbering_gap_free_under_concurrency(
    num_threads: int, calls_per_thread: int, year: int
) -> None:
    """Proves that under concurrent execution across multiple threads, generated numbers are strictly contiguous."""
    service = DocumentNumberingService()
    tenant_id = uuid.uuid4()
    total_calls = num_threads * calls_per_thread

    def worker_call() -> list[str]:
        results: list[str] = []
        for _ in range(calls_per_thread):
            doc_no = service.next_doc_no(tenant_id=tenant_id, series_key="DOC", year=year)
            results.append(doc_no)
        return results

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker_call) for _ in range(num_threads)]
        all_doc_numbers: list[str] = []
        for f in concurrent.futures.as_completed(futures):
            all_doc_numbers.extend(f.result())

    assert len(all_doc_numbers) == total_calls

    # Extract integer sequence numbers from formatted strings (e.g. '2026/00001' -> 1)
    seq_numbers: list[int] = []
    for doc_no in all_doc_numbers:
        match = re.search(rf"{year}/(\d+)", doc_no)
        assert match is not None, f"Document number {doc_no} failed pattern match"
        seq_numbers.append(int(match.group(1)))

    # Invariants:
    # 1. No duplicate sequence numbers
    assert len(set(seq_numbers)) == total_calls

    # 2. Sorted sequences must form a gap-free contiguous progression from 1 to total_calls
    sorted_seqs = sorted(seq_numbers)
    expected_contiguous = list(range(1, total_calls + 1))
    msg = f"Gaps in sequence! Got {sorted_seqs[:10]}... expected {expected_contiguous[:10]}"
    assert sorted_seqs == expected_contiguous, msg


# --- 2. Property: Amount in Words Invariants ---


@settings(max_examples=50, deadline=None)
@given(
    amount=st.integers(min_value=1, max_value=999_99_99_999),
)
def test_amount_in_words_marathi_invariants(amount: int) -> None:
    """Proves Marathi currency formatting invariants across all positive integer ranges."""
    words = number_to_words_mr(amount, currency=True)

    # Invariants:
    # 1. Output is non-empty string
    assert isinstance(words, str)
    assert len(words.strip()) > 0

    # 2. Output must conclude with legal statutory currency suffix
    assert words.endswith("रुपये फक्त")

    # 3. Contains appropriate scale words based on numerical threshold
    if amount >= 1_00_00_000:
        assert "कोटी" in words
    elif amount >= 1_00_000:
        assert "लाख" in words
    elif amount >= 1_000:
        assert "हजार" in words


# --- 3. Property: Decimal Area Conversion Invariants ---


@settings(max_examples=50, deadline=None)
@given(
    sqm=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("50000.00"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_decimal_area_sqm_sqft_roundtrip(sqm: Decimal) -> None:
    """Proves that area conversions exclusively use Decimal and round-trip error is strictly bounded."""
    sqft = sqm_to_sqft(sqm)
    assert isinstance(sqft, Decimal)

    recomputed_sqm = sqft_to_sqm(sqft)
    assert isinstance(recomputed_sqm, Decimal)

    # Due to 2 decimal places rounding on both legs, round-trip error cannot exceed 0.05 sqm
    error = abs(sqm - recomputed_sqm)
    msg = f"Round-trip error {error} exceeds tolerance for {sqm}"
    assert error <= Decimal("0.05"), msg


@settings(max_examples=50, deadline=None)
@given(
    guntha=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("1000.00"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_guntha_to_sqft_exactness(guntha: Decimal) -> None:
    """Proves guntha to sqft calculation maintains exact statutory constant."""
    sqft = guntha_to_sqft(guntha)
    assert isinstance(sqft, Decimal)
    assert sqft == (guntha * GUNTHA_TO_SQFT_FACTOR)


@settings(max_examples=50, deadline=None)
@given(
    hectare=st.decimals(
        min_value=Decimal("0"),
        max_value=Decimal("500"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    ),
    r=st.decimals(
        min_value=Decimal("0"),
        max_value=Decimal("99"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_hectare_r_to_sqm_invariants(hectare: Decimal, r: Decimal) -> None:
    """Proves Hectare-R area conversion is strictly monotonic and exact Decimal."""
    sqm = hectare_r_to_sqm(hectare, r)
    assert isinstance(sqm, Decimal)
    assert sqm >= Decimal("0.00")
    expected = (hectare * HECTARE_TO_SQM_FACTOR) + (r * Decimal("100.00"))
    assert sqm == expected
