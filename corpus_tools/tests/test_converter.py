"""Integration tests for batch converter over the 20 synthetic sample files."""

import json
from pathlib import Path
from corpus_tools.converter import batch_convert


def test_batch_convert_20_synthetic_files(tmp_path: Path) -> None:
    """Verifies that the batch converter runs across all 20 synthetic files."""
    fixtures_dir = Path(__file__).parent.parent / "fixtures" / "synthetic_samples"
    assert fixtures_dir.exists()

    input_files = list(fixtures_dir.glob("*.txt"))
    assert len(input_files) == 20, f"Expected 20 synthetic sample files, found {len(input_files)}"

    out_dir = tmp_path / "converted_output"
    reports = batch_convert(fixtures_dir, out_dir)

    assert len(reports) == 20
    assert all(r.success for r in reports)

    # Verify report JSON was created
    report_file = out_dir / "conversion_report.json"
    assert report_file.exists()

    data = json.loads(report_file.read_text(encoding="utf-8"))
    assert len(data) == 20

    # Verify Latin-in-Kruti warning flagged on sample 19
    sample_19 = next((r for r in reports if "19_latin" in r.file_name), None)
    assert sample_19 is not None
    assert len(sample_19.warnings) > 0
    warning_types = [w["type"] for w in sample_19.warnings]
    assert "PAN" in warning_types or "10_12_DIGIT_ID" in warning_types

