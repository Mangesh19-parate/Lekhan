"""Golden-file and lint verification tests for Wave 2 Templates (28 Document Types, 56 Templates).

Validates:
1. Wave 2 Starter: Marathi Release Deed (release_deed_mr)
2. All 28 Wave 2 Document Types in Marathi and English (56 templates):
   - gift_deed (mr, en)
   - exchange_deed (mr, en)
   - transfer_deed (mr, en)
   - house_sale_deed (mr, en)
   - family_partition (mr, en)
   - family_settlement (mr, en)
   - will (mr, en)
   - property_distribution_agreement (mr, en)
   - possession_letter (mr, en)
   - possession_receipt (mr, en)
   - property_handover (mr, en)
   - rights_transfer (mr, en)
   - property_rights_declaration (mr, en)
   - general_agreement (mr, en)
   - leave_and_licence (mr, en)
   - rent_residential (mr, en)
   - rent_shop (mr, en)
   - rent_commercial (mr, en)
   - flat_leave_licence (mr, en)
   - agri_lease (mr, en)
   - mortgage_deed (mr, en)
   - mortgage_agreement (mr, en)
   - simple_mortgage (mr, en)
   - usufructuary_mortgage (mr, en)
   - memorandum_of_deposit_of_title_deeds (mr, en)
   - loan_security_document (mr, en)
   - special_poa (mr, en)
   - irrevocable_poa (mr, en)

Verification assertions:
- Schema v1 manifest validation & compilation
- Status is "draft" pending advocate approval
- OpenXML Legal paper size (12240x20160 dxa) and centered PAGE footer
- Clause library integration (app.templates.clauses)
- Zero leftover PII or client data
- Zero linter errors and can_approve is True
"""

from __future__ import annotations

import json
from pathlib import Path

import docx
import pytest

from app.templates.compiler import ManifestCompiler
from app.templates.lint import DocxLinter

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates-library"

WAVE_2_DOC_TYPES = [
    "gift_deed",
    "exchange_deed",
    "transfer_deed",
    "house_sale_deed",
    "family_partition",
    "family_settlement",
    "will",
    "property_distribution_agreement",
    "possession_letter",
    "possession_receipt",
    "property_handover",
    "rights_transfer",
    "property_rights_declaration",
    "general_agreement",
    "leave_and_licence",
    "rent_residential",
    "rent_shop",
    "rent_commercial",
    "flat_leave_licence",
    "agri_lease",
    "mortgage_deed",
    "mortgage_agreement",
    "simple_mortgage",
    "usufructuary_mortgage",
    "memorandum_of_deposit_of_title_deeds",
    "loan_security_document",
    "special_poa",
    "irrevocable_poa",
]

WAVE_2_ALL_TEMPLATE_IDS = [
    f"{doc_type}_{lang}" for doc_type in WAVE_2_DOC_TYPES for lang in ("mr", "en")
]


def test_wave_2_template_release_deed_mr_lint_and_manifest() -> None:
    """Verifies that starter template release_deed_mr manifest compiles and template.docx passes lint cleanly."""
    tmpl_dir = TEMPLATES_DIR / "release_deed_mr"
    manifest_path = tmpl_dir / "manifest.json"
    docx_path = tmpl_dir / "template.docx"

    assert manifest_path.exists(), "Manifest file missing for release_deed_mr"
    assert docx_path.exists(), "DOCX file missing for release_deed_mr"

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == "release_deed_mr"
    assert compiled.document_type == "release_deed"
    assert compiled.language == "mr"
    assert "releasors" in compiled.parties
    assert "releasees" in compiled.parties

    # Run DocxLinter
    report = DocxLinter().lint(docx_path.read_bytes(), manifest=raw_manifest)
    assert report.can_approve is True, f"Lint errors: {report.errors}"
    assert len(report.leftover_data) == 0, f"Leftover PII found: {report.leftover_data}"
    assert len(report.errors) == 0, f"Errors: {report.errors}"


@pytest.mark.golden
@pytest.mark.parametrize("tmpl_id", WAVE_2_ALL_TEMPLATE_IDS)
def test_wave_2_templates_lint_and_manifest(tmpl_id: str) -> None:
    """Parametrized golden test across all 56 Wave 2 templates."""
    tmpl_dir = TEMPLATES_DIR / tmpl_id
    manifest_path = tmpl_dir / "manifest.json"
    docx_path = tmpl_dir / "template.docx"

    assert manifest_path.exists(), f"Manifest file missing for {tmpl_id}"
    assert docx_path.exists(), f"DOCX file missing for {tmpl_id}"

    # 1. Manifest Schema v1 validation & compilation
    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == tmpl_id
    assert raw_manifest.get("manifest_schema") == 1
    assert raw_manifest.get("version") == 1
    assert raw_manifest.get("status") == "draft", f"{tmpl_id} must be draft until lawyer approves"
    assert raw_manifest.get("page_size") == "legal"

    # Clause library verification
    assert "clauses" in raw_manifest
    assert len(raw_manifest["clauses"]) > 0, f"No clause library reuse in {tmpl_id}"

    # 2. OpenXML Layout & Page Setup Verification
    docx_bytes = docx_path.read_bytes()
    doc = docx.Document(docx_path)
    section = doc.sections[0]
    # Legal paper: 8.5 x 14 in (7772400 x 12801600 EMU)
    assert section.page_width == 7772400, f"Width not Legal size in {tmpl_id}"
    assert section.page_height == 12801600, f"Height not Legal size in {tmpl_id}"

    # Footer verification
    footer_text = "".join(p.text for p in section.footer.paragraphs)
    if raw_manifest.get("language") == "mr":
        assert "पान क्र." in footer_text
    else:
        assert "Page" in footer_text

    # 3. Master DocxLinter Audit
    report = DocxLinter().lint(docx_bytes, manifest=raw_manifest)
    assert report.can_approve is True, f"Lint failed on {tmpl_id}: {report.errors}"
    assert len(report.leftover_data) == 0, f"Leftover PII found in {tmpl_id}: {report.leftover_data}"
    assert len(report.errors) == 0, f"Errors in {tmpl_id}: {report.errors}"
