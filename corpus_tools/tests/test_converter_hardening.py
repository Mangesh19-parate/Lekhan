"""Unit tests for Kruti Dev converter hardening, round-trip scoring, and review queue."""

from pathlib import Path
import pytest

from app.lang_packs.encodings.kruti import KrutiConverter
from corpus_tools.review_queue import ReviewQueue


ROOT_DIR = Path(__file__).parent.parent.parent


def test_roundtrip_conversion_and_scoring() -> None:
    """Verifies that Kruti text converts to Unicode and scores accurately on reverse conversion."""
    sample_kruti = "djkji= ekSts lksusxko [kljk dzekad 45@2"
    score, reconstructed, anomalies = KrutiConverter.compute_roundtrip_score(sample_kruti)

    assert score >= 90.0, f"Expected roundtrip score >= 90%, got {score}%"
    assert len(reconstructed) > 0


def test_detect_latin_in_kruti_warning() -> None:
    """Verifies that Latin fragments typed in Kruti font are flagged for human review."""
    sample_file = (
        ROOT_DIR
        / "corpus_tools"
        / "fixtures"
        / "synthetic_samples"
        / "19_latin_in_kruti_warning_pan.txt"
    )
    assert sample_file.exists(), f"Synthetic sample missing at {sample_file}"

    text = sample_file.read_text(encoding="utf-8")
    warnings = KrutiConverter.detect_latin_in_kruti(text)

    assert len(warnings) > 0
    # Must flag PAN / ID / Keyword
    detected_types = {w.pattern_type for w in warnings}
    assert any(t in detected_types for t in ("PAN_PATTERN", "LATIN_KEYWORD", "ALPHANUMERIC_CODE"))


def test_review_queue_lifecycle(tmp_path: Path) -> None:
    """Verifies candidate enqueuing, human approval requirement, and rejection."""
    queue_file = tmp_path / "test_review_queue.json"
    queue = ReviewQueue(storage_path=queue_file)

    # 1. Enqueue candidate
    item = queue.add_candidate(
        item_id="sample_deed_01",
        source_file="sample_01.docx",
        roundtrip_score=98.5,
        anomalies=[],
    )
    assert item.status == "pending"
    assert len(queue.list_pending()) == 1

    # 2. Rejection without reviewer must fail
    with pytest.raises(ValueError):
        queue.approve("sample_deed_01", reviewer="")

    # 3. Legitimate human reviewer approves
    approved_item = queue.approve("sample_deed_01", reviewer="advocate_shinde", notes="Verified by human eye")
    assert approved_item.status == "approved"
    assert approved_item.reviewer == "advocate_shinde"
    assert len(queue.list_pending()) == 0

    # 4. Reject another candidate
    queue.add_candidate("sample_deed_02", "sample_02.docx", 91.0)
    rejected_item = queue.reject("sample_deed_02", reviewer="advocate_shinde", reason="Broken matras in paragraph 4")
    assert rejected_item.status == "rejected"

    summary = queue.get_summary()
    assert summary["total_candidates"] == 2
    assert summary["approved"] == 1
    assert summary["rejected"] == 1

