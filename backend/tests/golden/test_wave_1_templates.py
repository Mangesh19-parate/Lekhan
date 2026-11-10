"""Golden-file and lint verification tests for Wave 1 Templates 1-3.

Validates:
1. Template 1: Marathi Plot Sale Deed (sale_deed_plot_mr)
2. Template 2: Marathi Plot Agreement to Sell (agreement_to_sell_plot_mr)
3. Template 3: English Flat Sale Deed (sale_deed_flat_en)
"""

import io
import json
from pathlib import Path
import zipfile
from decimal import Decimal
import pytest

from app.lang_packs import get_language_pack
from app.templates.compiler import ManifestCompiler, ManifestRuntime
from app.templates.lint import DocxLinter

TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "templates-library"


# ---------------------------------------------------------------------------
# Template 1: Marathi Plot Sale Deed (sale_deed_plot_mr)
# ---------------------------------------------------------------------------

def test_template_1_sale_deed_plot_mr_lint_and_manifest() -> None:
    """Verifies that Template 1 manifest is valid Schema v1 and template.docx passes lint cleanly."""
    tmpl_dir = TEMPLATES_DIR / "sale_deed_plot_mr"
    manifest_path = tmpl_dir / "manifest.json"
    docx_path = tmpl_dir / "template.docx"

    assert manifest_path.exists()
    assert docx_path.exists()

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == "sale_deed_plot_mr"

    report = DocxLinter().lint(docx_path.read_bytes(), manifest=raw_manifest)
    assert report.can_approve is True
    assert len(report.leftover_data) == 0
    assert len(report.errors) == 0


# ---------------------------------------------------------------------------
# Template 2: Marathi Plot Agreement to Sell (agreement_to_sell_plot_mr)
# ---------------------------------------------------------------------------

def test_template_2_agreement_to_sell_plot_mr_lint_and_manifest() -> None:
    """Verifies that Template 2 manifest compiles and template.docx passes lint cleanly."""
    tmpl_dir = TEMPLATES_DIR / "agreement_to_sell_plot_mr"
    manifest_path = tmpl_dir / "manifest.json"
    docx_path = tmpl_dir / "template.docx"

    assert manifest_path.exists()
    assert docx_path.exists()

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == "agreement_to_sell_plot_mr"
    assert "financial.balance_due" in compiled.derived_fields

    report = DocxLinter().lint(docx_path.read_bytes(), manifest=raw_manifest)
    assert report.can_approve is True
    assert len(report.leftover_data) == 0
    assert len(report.errors) == 0

    # Test runtime derived math
    runtime = ManifestRuntime()
    input_data = {
        "property": {"area_sqm": Decimal("150.00")},
        "financial": {
            "total_consideration": Decimal("3000000"),
            "earnest_amount": Decimal("600000"),
            "has_bank_loan": True,
        },
        "terms": {"months_to_complete": 3},
    }
    res = runtime.evaluate_derived_fields(compiled, input_data)
    assert res["financial"]["balance_due"] == Decimal("2400000")


# ---------------------------------------------------------------------------
# Template 3: English Flat Sale Deed (sale_deed_flat_en)
# ---------------------------------------------------------------------------

def test_template_3_sale_deed_flat_en_lint_and_manifest() -> None:
    """Verifies that Template 3 English flat sale deed compiles and passes lint cleanly."""
    tmpl_dir = TEMPLATES_DIR / "sale_deed_flat_en"
    manifest_path = tmpl_dir / "manifest.json"
    docx_path = tmpl_dir / "template.docx"

    assert manifest_path.exists()
    assert docx_path.exists()

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == "sale_deed_flat_en"
    assert compiled.raw_manifest["language"] == "en"

    report = DocxLinter().lint(docx_path.read_bytes(), manifest=raw_manifest)
    assert report.can_approve is True
    assert len(report.leftover_data) == 0
    assert len(report.errors) == 0

    # Test runtime derived math and English language pack
    runtime = ManifestRuntime()
    en_pack = get_language_pack("en")

    input_data = {
        "property": {"carpet_area_sqm": Decimal("85.50")},
        "financial": {
            "total_price": Decimal("6500000"),
            "advance_paid": Decimal("1500000"),
        },
    }
    res = runtime.evaluate_derived_fields(compiled, input_data)
    assert res["financial"]["balance_amount"] == Decimal("5000000")

    words = en_pack.number_to_words(res["financial"]["balance_amount"])
    assert words == "Rupees Fifty Lakh Only"


# ---------------------------------------------------------------------------
# Template 4: Marathi Flat Sale Deed (sale_deed_flat_mr)
# ---------------------------------------------------------------------------

def test_template_4_sale_deed_flat_mr_lint_and_manifest() -> None:
    """Verifies that Template 4 Marathi flat sale deed compiles and passes lint cleanly."""
    tmpl_dir = TEMPLATES_DIR / "sale_deed_flat_mr"
    manifest_path = tmpl_dir / "manifest.json"
    docx_path = tmpl_dir / "template.docx"

    assert manifest_path.exists()
    assert docx_path.exists()

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == "sale_deed_flat_mr"
    assert "financial.balance_amount" in compiled.derived_fields

    report = DocxLinter().lint(docx_path.read_bytes(), manifest=raw_manifest)
    assert report.can_approve is True
    assert len(report.leftover_data) == 0
    assert len(report.errors) == 0

    runtime = ManifestRuntime()
    input_data = {
        "property": {"carpet_area_sqm": Decimal("75.00")},
        "financial": {
            "total_consideration": Decimal("4500000"),
            "earnest_advance": Decimal("1000000"),
        },
    }
    res = runtime.evaluate_derived_fields(compiled, input_data)
    assert res["financial"]["balance_amount"] == Decimal("3500000")


# ---------------------------------------------------------------------------
# Template 5: Marathi Commercial Shop Sale Deed (sale_deed_shop_mr)
# ---------------------------------------------------------------------------

def test_template_5_sale_deed_shop_mr_lint_and_manifest() -> None:
    """Verifies that Template 5 commercial shop deed compiles and passes lint cleanly."""
    tmpl_dir = TEMPLATES_DIR / "sale_deed_shop_mr"
    manifest_path = tmpl_dir / "manifest.json"
    docx_path = tmpl_dir / "template.docx"

    assert manifest_path.exists()
    assert docx_path.exists()

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == "sale_deed_shop_mr"

    report = DocxLinter().lint(docx_path.read_bytes(), manifest=raw_manifest)
    assert report.can_approve is True
    assert len(report.leftover_data) == 0
    assert len(report.errors) == 0

    runtime = ManifestRuntime()
    input_data = {
        "property": {"builtup_area_sqm": Decimal("35.00")},
        "financial": {
            "total_consideration": Decimal("2800000"),
            "earnest_advance": Decimal("500000"),
        },
    }
    res = runtime.evaluate_derived_fields(compiled, input_data)
    assert res["financial"]["balance_amount"] == Decimal("2300000")


# ---------------------------------------------------------------------------
# Template 6: Marathi General Power of Attorney (general_poa_mr)
# ---------------------------------------------------------------------------

def test_template_6_general_poa_mr_lint_and_manifest() -> None:
    """Verifies that Template 6 General POA compiles and passes lint cleanly."""
    tmpl_dir = TEMPLATES_DIR / "general_poa_mr"
    manifest_path = tmpl_dir / "manifest.json"
    docx_path = tmpl_dir / "template.docx"

    assert manifest_path.exists()
    assert docx_path.exists()

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == "general_poa_mr"

    report = DocxLinter().lint(docx_path.read_bytes(), manifest=raw_manifest)
    assert report.can_approve is True
    assert len(report.leftover_data) == 0
    assert len(report.errors) == 0


# ---------------------------------------------------------------------------
# Template 7: Marathi Agricultural Land Sale Deed (sale_deed_agricultural_mr)
# ---------------------------------------------------------------------------

def test_template_7_sale_deed_agricultural_mr_lint_and_manifest() -> None:
    """Verifies that Template 7 Agricultural Sale Deed compiles and passes lint cleanly."""
    tmpl_dir = TEMPLATES_DIR / "sale_deed_agricultural_mr"
    manifest_path = tmpl_dir / "manifest.json"
    docx_path = tmpl_dir / "template.docx"

    assert manifest_path.exists()
    assert docx_path.exists()

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == "sale_deed_agricultural_mr"
    assert "financial.balance_amount" in compiled.derived_fields

    report = DocxLinter().lint(docx_path.read_bytes(), manifest=raw_manifest)
    assert report.can_approve is True
    assert len(report.leftover_data) == 0
    assert len(report.errors) == 0

    runtime = ManifestRuntime()
    input_data = {
        "property": {"area_hectare_r": "1.20"},
        "financial": {
            "total_consideration": Decimal("4500000"),
            "earnest_advance": Decimal("1000000"),
        },
    }
    res = runtime.evaluate_derived_fields(compiled, input_data)
    assert res["financial"]["balance_amount"] == Decimal("3500000")


# ---------------------------------------------------------------------------
# Template 8: Marathi Flat Agreement to Sell (agreement_to_sell_flat_mr)
# ---------------------------------------------------------------------------

def test_template_8_agreement_to_sell_flat_mr_lint_and_manifest() -> None:
    """Verifies that Template 8 Marathi Flat Agreement to Sell compiles and passes lint cleanly."""
    tmpl_dir = TEMPLATES_DIR / "agreement_to_sell_flat_mr"
    manifest_path = tmpl_dir / "manifest.json"
    docx_path = tmpl_dir / "template.docx"

    assert manifest_path.exists()
    assert docx_path.exists()

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == "agreement_to_sell_flat_mr"
    assert "financial.balance_due" in compiled.derived_fields

    report = DocxLinter().lint(docx_path.read_bytes(), manifest=raw_manifest)
    assert report.can_approve is True
    assert len(report.leftover_data) == 0
    assert len(report.errors) == 0

    runtime = ManifestRuntime()
    input_data = {
        "property": {"carpet_area_sqm": Decimal("65.00")},
        "financial": {
            "total_consideration": Decimal("4000000"),
            "earnest_amount": Decimal("500000"),
        },
    }
    res = runtime.evaluate_derived_fields(compiled, input_data)
    assert res["financial"]["balance_due"] == Decimal("3500000")


# ---------------------------------------------------------------------------
# Template 9: English Flat Agreement to Sell (agreement_to_sell_flat_en)
# ---------------------------------------------------------------------------

def test_template_9_agreement_to_sell_flat_en_lint_and_manifest() -> None:
    """Verifies that Template 9 English Flat Agreement to Sell compiles and passes lint cleanly."""
    tmpl_dir = TEMPLATES_DIR / "agreement_to_sell_flat_en"
    manifest_path = tmpl_dir / "manifest.json"
    docx_path = tmpl_dir / "template.docx"

    assert manifest_path.exists()
    assert docx_path.exists()

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == "agreement_to_sell_flat_en"
    assert "financial.balance_due" in compiled.derived_fields

    report = DocxLinter().lint(docx_path.read_bytes(), manifest=raw_manifest)
    assert report.can_approve is True
    assert len(report.leftover_data) == 0
    assert len(report.errors) == 0

    runtime = ManifestRuntime()
    input_data = {
        "property": {"carpet_area_sqm": Decimal("80.00")},
        "financial": {
            "total_consideration": Decimal("5500000"),
            "earnest_amount": Decimal("1000000"),
        },
    }
    res = runtime.evaluate_derived_fields(compiled, input_data)
    assert res["financial"]["balance_due"] == Decimal("4500000")


# ---------------------------------------------------------------------------
# Template 10: English General Power of Attorney (general_poa_en)
# ---------------------------------------------------------------------------

def test_template_10_general_poa_en_lint_and_manifest() -> None:
    """Verifies that Template 10 English General POA compiles and passes lint cleanly."""
    tmpl_dir = TEMPLATES_DIR / "general_poa_en"
    manifest_path = tmpl_dir / "manifest.json"
    docx_path = tmpl_dir / "template.docx"

    assert manifest_path.exists()
    assert docx_path.exists()

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == "general_poa_en"

    report = DocxLinter().lint(docx_path.read_bytes(), manifest=raw_manifest)
    assert report.can_approve is True
    assert len(report.leftover_data) == 0
    assert len(report.errors) == 0


# ---------------------------------------------------------------------------
# OpenXML Layout Compliance (PAGE Field and Legal Page Size for All 10)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "tmpl_rel_path",
    [
        "sale_deed_plot_mr/template.docx",
        "agreement_to_sell_plot_mr/template.docx",
        "sale_deed_flat_en/template.docx",
        "sale_deed_flat_mr/template.docx",
        "sale_deed_shop_mr/template.docx",
        "general_poa_mr/template.docx",
        "sale_deed_agricultural_mr/template.docx",
        "agreement_to_sell_flat_mr/template.docx",
        "agreement_to_sell_flat_en/template.docx",
        "general_poa_en/template.docx",
    ],
)
def test_openxml_compliance(tmpl_rel_path: str) -> None:
    """Verifies that all Wave 1 templates possess Legal paper size and PAGE footers."""
    docx_file = TEMPLATES_DIR / tmpl_rel_path
    with zipfile.ZipFile(docx_file, "r") as zf:
        # 1. Forward slashes check
        for info in zf.infolist():
            assert "\\" not in info.filename, f"Invalid backslash in ZIP path: {info.filename}"

        # 2. Check footer PAGE field
        footer_xml = zf.read("word/footer1.xml").decode("utf-8")
        assert 'w:instr="PAGE"' in footer_xml

        # 3. Check Legal paper dimensions (12240 x 20160 dxa)
        doc_xml = zf.read("word/document.xml").decode("utf-8")
        assert 'w:w="12240"' in doc_xml and 'w:h="20160"' in doc_xml

