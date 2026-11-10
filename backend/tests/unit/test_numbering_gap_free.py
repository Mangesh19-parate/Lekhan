"""50-Parallel Gap-Free Numbering Stress Test (PRD FR-12, Features F-055, ADR 012).

Tests:
1. 50 parallel concurrent workers request sequential document numbers.
2. Resulting sequence must contain exactly 1..50 with ZERO GAPS and ZERO DUPLICATES.
3. Multi-tenant isolation: Tenant A and Tenant B maintain independent gap-free sequences.
"""

import concurrent.futures
import uuid

from app.numbering.service import DocumentNumberingService


def test_gap_free_numbering_50_parallel() -> None:
    """Verifies that 50 concurrent threads produce strictly gap-free numbers without collision."""
    service = DocumentNumberingService()
    tenant_id = uuid.uuid4()
    worker_count = 50

    def generate_number(idx: int) -> str:
        return service.next_doc_no(tenant_id=tenant_id, series_key="DOC", year=2026)

    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(generate_number, i) for i in range(worker_count)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # 1. Exact count check
    assert len(results) == worker_count

    # 2. Zero duplicates check
    unique_numbers = set(results)
    assert (
        len(unique_numbers) == worker_count
    ), f"Duplicate detected: {len(results) - len(unique_numbers)} collisions"

    # 3. Gap-free sequence check (must be exactly 1 to 50)
    sequences = sorted([int(num.split("/")[-1]) for num in results])
    expected_sequences = list(range(1, worker_count + 1))
    assert sequences == expected_sequences, f"Gaps detected in numbering sequence: {sequences}"


def test_tenant_isolation_numbering() -> None:
    """Verifies that each tenant gets an independent sequence counter."""
    service = DocumentNumberingService()
    tenant_1 = uuid.uuid4()
    tenant_2 = uuid.uuid4()

    n1_1 = service.next_doc_no(tenant_id=tenant_1, series_key="DOC", year=2026)
    n1_2 = service.next_doc_no(tenant_id=tenant_1, series_key="DOC", year=2026)

    n2_1 = service.next_doc_no(tenant_id=tenant_2, series_key="DOC", year=2026)

    assert n1_1 == "2026/00001"
    assert n1_2 == "2026/00002"
    assert n2_1 == "2026/00001"  # Tenant 2 starts independently at 1


def test_series_and_prefix_formatting() -> None:
    """Tests custom series and prefixes."""
    service = DocumentNumberingService()
    tenant_id = uuid.uuid4()

    # Custom series
    deed_no = service.next_doc_no(tenant_id=tenant_id, series_key="DEED", year=2026)
    assert deed_no == "DEED/2026/00001"

    # Custom prefix
    custom_no = service.next_doc_no(
        tenant_id=tenant_id, series_key="DOC", year=2026, prefix="LEKHAN-NAGPUR"
    )
    assert custom_no == "LEKHAN-NAGPUR/2026/00001"
