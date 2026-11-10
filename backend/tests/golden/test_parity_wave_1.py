"""Parity Golden Tests for all 10 Wave 1 Templates (ARCHITECTURE.md Section 6, Week 18).

Verifies layout and structural parity across all 10 templates:
1. Legal paper size (12240 x 20160 dxa).
2. Dynamic PAGE footer fields in footer1.xml.
3. Essential clause structure (parties, property schedule, consideration, witnesses).
4. Zero legacy Kruti Dev or 8-bit fonts.
"""

from pathlib import Path
import pytest

from corpus_tools.parity_runner import ParityRunner

TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "templates-library"


def test_wave_1_templates_parity_all_10() -> None:
    """Verifies layout and typography parity for all 10 Wave 1 approved templates."""
    runner = ParityRunner()
    reports = runner.run_all_wave_1(templates_dir=TEMPLATES_DIR)

    assert len(reports) == 10, f"Expected 10 Wave 1 templates, found {len(reports)}"

    failed_templates: list[str] = []
    for r in reports:
        if not r.parity_passed:
            failed_templates.append(f"{r.template_id}: {'; '.join(r.notes)}")

    assert len(failed_templates) == 0, f"Templates failed layout parity: {failed_templates}"


@pytest.mark.parametrize(
    "template_id",
    [
        "sale_deed_plot_mr",
        "agreement_to_sell_plot_mr",
        "sale_deed_flat_en",
        "sale_deed_flat_mr",
        "sale_deed_shop_mr",
        "sale_deed_agricultural_mr",
        "agreement_to_sell_flat_mr",
        "agreement_to_sell_flat_en",
        "general_poa_mr",
        "general_poa_en",
    ],
)
def test_individual_template_parity(template_id: str) -> None:
    """Individual parity assertion per Wave 1 template."""
    docx_file = TEMPLATES_DIR / template_id / "template.docx"
    assert docx_file.exists(), f"Missing template DOCX: {docx_file}"

    runner = ParityRunner()
    report = runner.analyze_template_docx(template_id, docx_file.read_bytes())

    assert report.is_legal_size is True
    assert report.has_page_footer_field is True
    assert len(report.legacy_fonts_detected) == 0
    assert report.paragraph_count >= 5
    assert report.parity_passed is True

