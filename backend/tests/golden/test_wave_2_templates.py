"""Golden-file and lint verification tests for Wave 2 Templates Starter (Plan Week 23).

Validates:
1. Wave 2 Template 1: Marathi Release Deed / Relinquishment (release_deed_mr)
   - Schema v1 manifest validation
   - Clean docx tags with zero split runs
   - Zero leftover client PII
   - Legal paper size (12240x20160 dxa) and centered PAGE footer
"""

from __future__ import annotations

import json
from pathlib import Path

from app.templates.compiler import ManifestCompiler
from app.templates.lint import DocxLinter

TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "templates-library"


def test_wave_2_template_release_deed_mr_lint_and_manifest() -> None:
    """Verifies that release_deed_mr manifest compiles and template.docx passes lint cleanly."""
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
