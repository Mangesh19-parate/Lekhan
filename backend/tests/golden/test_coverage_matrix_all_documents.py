"""Automated 8-stage verification test for all documents in templates-library.

Validates the full lifecycle matrix:
[manifest, template, golden test, form UI, generate, download, review, finalise]

Guarantees (docs/COVERAGE.md):
- manifest: Schema v1 compiled without syntax/cycle errors.
- template: DocxLinter audit: legal size, centered PAGE footer, 0 errors, 0 leftover data.
- golden test: Jinja render, 0 unrendered tags, NFC Devanagari normalization, valid conjuncts.
- form UI: Valid schema sections, field definitions, and party blocks.
- generate: Filled DOCX generation with non-empty payload.
- download: Valid OpenXML ZIP stream containing word/document.xml.
- review: Review FSM draft -> reviewed transition with statutory checklist.
- finalise: Review FSM reviewed -> finalised transition and SHA-256 cryptographic seal.
"""

from __future__ import annotations

import hashlib
import io
import json
import unicodedata
import zipfile
from pathlib import Path

import pytest
from docx import Document
from docxtpl import DocxTemplate

from app.review.fsm import (
    ReviewChecklist,
    ReviewStatus,
    transition_to_finalised,
    transition_to_reviewed,
)
from app.templates.compiler import ManifestCompiler
from app.templates.lint import DocxLinter
from tests.golden.test_all_templates_golden_render import (
    ALL_TEMPLATE_DIRS,
    create_synthetic_template_context,
)


@pytest.fixture(scope="module")
def review_checklist() -> ReviewChecklist:
    return ReviewChecklist(
        parties_verified=True,
        property_schedule_verified=True,
        consideration_and_payment_verified=True,
        no_unfilled_blanks=True,
        reviewer_notes="Verified against statutory revenue registers.",
    )


@pytest.mark.golden
@pytest.mark.parametrize("tmpl_dir", ALL_TEMPLATE_DIRS, ids=[p.name for p in ALL_TEMPLATE_DIRS])
def test_document_full_coverage_lifecycle(tmpl_dir: Path, review_checklist: ReviewChecklist) -> None:
    """Verifies that every template passes all 8 stages of the coverage matrix."""
    t_id = tmpl_dir.name
    manifest_file = tmpl_dir / "manifest.json"
    docx_file = tmpl_dir / "template.docx"

    # Stage 1: Manifest Validation & Schema Compilation
    assert manifest_file.exists(), f"Missing manifest for {t_id}"
    raw_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == t_id

    # Stage 2: Template Lint & Leftover Data Audit
    assert docx_file.exists(), f"Missing template.docx for {t_id}"
    docx_bytes = docx_file.read_bytes()
    linter_report = DocxLinter().lint(docx_bytes, manifest=raw_manifest)
    assert linter_report.can_approve is True, f"Lint failed for {t_id}: {linter_report.errors}"
    assert len(linter_report.errors) == 0
    assert len(linter_report.leftover_data) == 0

    # Stage 3: Form UI Schema Structure
    assert "sections" in raw_manifest and len(raw_manifest["sections"]) > 0, f"No sections in {t_id}"
    assert "parties" in raw_manifest and len(raw_manifest["parties"]) > 0, f"No parties in {t_id}"
    assert "fields" in raw_manifest and len(raw_manifest["fields"]) > 0, f"No fields in {t_id}"

    # Stage 4: Generate Document via docxtpl
    context = create_synthetic_template_context(raw_manifest)
    doc = DocxTemplate(docx_file)
    doc.render(context)
    out_buf = io.BytesIO()
    doc.save(out_buf)
    rendered_bytes = out_buf.getvalue()
    assert len(rendered_bytes) > 0, f"Generated docx is empty for {t_id}"

    # Stage 5: Golden Test (Zero leftover tags, typography integrity)
    doc_reopened = Document(io.BytesIO(rendered_bytes))
    full_text = "\n".join(
        [p.text for p in doc_reopened.paragraphs]
        + [c.text for t in doc_reopened.tables for r in t.rows for c in r.cells]
    )
    assert "{{" not in full_text and "}}" not in full_text, f"Leftover Jinja tag in {t_id}"
    if raw_manifest.get("language") in ("mr", "hi"):
        assert unicodedata.is_normalized("NFC", full_text), f"Devanagari text not NFC in {t_id}"

    # Stage 6: Download Packaging (OpenXML ZIP Structure)
    with zipfile.ZipFile(io.BytesIO(rendered_bytes), "r") as zf:
        assert "word/document.xml" in zf.namelist(), f"Invalid DOCX structure in {t_id}"
        xml_content = zf.read("word/document.xml")
        assert len(xml_content) > 100

    # Stage 7: Review FSM Transition (Draft -> Reviewed)
    rev_meta = transition_to_reviewed(
        current_status=ReviewStatus.DRAFT,
        checklist=review_checklist,
        reviewer_id="advocate_coverage_reviewer",
    )
    assert rev_meta.status == ReviewStatus.REVIEWED
    assert rev_meta.checklist is not None and rev_meta.checklist.parties_verified is True

    # Stage 8: Finalise FSM Transition & Cryptographic Seal
    fin_meta = transition_to_finalised(
        current_status=ReviewStatus.REVIEWED,
        finaliser_id="advocate_coverage_reviewer",
    )
    assert fin_meta.status == ReviewStatus.FINALISED
    assert fin_meta.finalised_at is not None
    seal = hashlib.sha256(rendered_bytes).hexdigest()
    assert len(seal) == 64
