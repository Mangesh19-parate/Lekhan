"""Unit tests for DOCX template linting, structural safety, and leftover client data scanning."""

import io
import json
from pathlib import Path
import zipfile
import pytest

from app.templates.lint.fonts import audit_docx_fonts
from app.templates.lint.leftover_scanner import scan_docx_for_leftover_data
from app.templates.lint.linter import DocxLinter
from app.templates.lint.models import LintSeverity
from app.templates.lint.split_runs import repair_and_check_split_runs
from app.templates.lint.structural import (
    check_structural_safety,
    strip_external_relationships,
)


def create_minimal_docx_bytes(
    body_xml: str,
    extra_files: dict[str, bytes] | None = None,
) -> bytes:
    """Helper to synthesize valid minimal OpenXML DOCX bytes in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>"
        )
        zf.writestr("[Content_Types].xml", content_types)

        doc_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body>{body_xml}</w:body>"
            "</w:document>"
        )
        zf.writestr("word/document.xml", doc_xml)

        if extra_files:
            for fname, fbytes in extra_files.items():
                zf.writestr(fname, fbytes)

    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. Split-Run Tag Detection and Auto-Merging
# ---------------------------------------------------------------------------

def test_split_run_auto_merge_identical_formatting() -> None:
    """Verifies that tags split across runs with identical formatting are merged."""
    body = (
        "<w:p>"
        "<w:r><w:t>{{</w:t></w:r>"
        "<w:r><w:t>property.</w:t></w:r>"
        "<w:r><w:t>mouza}}</w:t></w:r>"
        "</w:p>"
    )
    docx_bytes = create_minimal_docx_bytes(body)
    repaired, merge_count, findings = repair_and_check_split_runs(docx_bytes)

    assert merge_count >= 1
    # Check that repaired document contains intact single-run tag
    with zipfile.ZipFile(io.BytesIO(repaired), "r") as zf:
        doc_content = zf.read("word/document.xml").decode("utf-8")
        assert "{{property.mouza}}" in doc_content


def test_split_run_conflicting_formatting_warning() -> None:
    """Verifies that split tags spanning different formatting emit a warning."""
    body = (
        "<w:p>"
        "<w:r><w:rPr><w:b/></w:rPr><w:t>{{property.</w:t></w:r>"
        "<w:r><w:rPr><w:i/></w:rPr><w:t>mouza}}</w:t></w:r>"
        "</w:p>"
    )
    docx_bytes = create_minimal_docx_bytes(body)
    _, _, findings = repair_and_check_split_runs(docx_bytes)

    assert any(f.code == "SPLIT_RUN_FORMATTING_CONFLICT" for f in findings)


# ---------------------------------------------------------------------------
# 2. Structural Safety Checks (Macros, Zip Bomb, External Rels)
# ---------------------------------------------------------------------------

def test_reject_macro_enabled_template() -> None:
    """Verifies rejection of macro-enabled files containing vbaProject.bin."""
    extra = {"word/vbaProject.bin": b"VBA-MACRO-DATA"}
    docx_bytes = create_minimal_docx_bytes("<w:p><w:r><w:t>Hello</w:t></w:r></w:p>", extra_files=extra)

    findings = check_structural_safety(docx_bytes)
    assert any(f.code == "MACRO_ENABLED_FILE" and f.severity == LintSeverity.ERROR for f in findings)


def test_reject_external_relationships() -> None:
    """Verifies rejection of documents containing external relationships."""
    rels_content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
        'Target="http://evil.com/leak" TargetMode="External"/>'
        "</Relationships>"
    ).encode("utf-8")
    extra = {"word/_rels/document.xml.rels": rels_content}
    docx_bytes = create_minimal_docx_bytes("<w:p><w:r><w:t>Hello</w:t></w:r></w:p>", extra_files=extra)

    findings = check_structural_safety(docx_bytes)
    assert any(f.code == "EXTERNAL_RELATIONSHIP_FOUND" for f in findings)

    # Verify that sanitizer strips external relationship
    sanitized = strip_external_relationships(docx_bytes)
    with zipfile.ZipFile(io.BytesIO(sanitized), "r") as zf:
        clean_rels = zf.read("word/_rels/document.xml.rels").decode("utf-8")
        assert "TargetMode" not in clean_rels


# ---------------------------------------------------------------------------
# 3. Leftover Client Data & PII Detection
# ---------------------------------------------------------------------------

def test_detect_leftover_pan_and_aadhaar() -> None:
    """Verifies that leftover PAN and Aadhaar literals outside tags are flagged."""
    # Synthetic PAN and Aadhaar literals outside tags
    body = (
        "<w:p><w:r><w:t>विक्रेत्याचा पॅन: ABCDE1234F आणि आधार: 9876 5432 1098</w:t></w:r></w:p>"
    )
    docx_bytes = create_minimal_docx_bytes(body)
    leftovers = scan_docx_for_leftover_data(docx_bytes)

    categories = [l.category for l in leftovers]
    assert "PAN" in categories
    assert "AADHAAR" in categories

    # Verify privacy masking (no raw data leaked in finding)
    pan_finding = next(l for l in leftovers if l.category == "PAN")
    assert "ABCDE1234F" not in pan_finding.masked_sample
    assert pan_finding.masked_sample.startswith("AB***")


def test_templated_placeholders_not_flagged_as_leftover() -> None:
    """Verifies that Jinja placeholders like {{ party.pan }} are not flagged as leftovers."""
    body = (
        "<w:p><w:r><w:t>पॅन: {{ party.pan }} आधार: {{ party.aadhaar_no }}</w:t></w:r></w:p>"
    )
    docx_bytes = create_minimal_docx_bytes(body)
    leftovers = scan_docx_for_leftover_data(docx_bytes)

    assert len(leftovers) == 0


# ---------------------------------------------------------------------------
# 4. Font Audit & Kruti Dev Legacy Detection
# ---------------------------------------------------------------------------

def test_detect_prohibited_kruti_dev_font() -> None:
    """Verifies that legacy Kruti Dev fonts are rejected with ERROR."""
    body = (
        '<w:p><w:r><w:rPr><w:rFonts w:ascii="Kruti Dev 010" w:cs="Kruti Dev 010"/></w:rPr>'
        '<w:t>djkji=</w:t></w:r></w:p>'
    )
    docx_bytes = create_minimal_docx_bytes(body)
    fonts, findings = audit_docx_fonts(docx_bytes)

    assert "Kruti Dev 010" in fonts
    assert any(f.code == "LEGACY_FONT_KRUTI_FOUND" and f.severity == LintSeverity.ERROR for f in findings)


# ---------------------------------------------------------------------------
# 5. Master DocxLinter & Manifest Tag Alignment
# ---------------------------------------------------------------------------

def test_docx_linter_undefined_tag_and_unused_field() -> None:
    """Verifies detection of undefined tags (error) and unused fields (warning)."""
    body = (
        "<w:p><w:r><w:t>{{ property.mouza }} आणि {{ undefined_secret_tag }}</w:t></w:r></w:p>"
    )
    manifest = {
        "manifest_schema": 1,
        "fields": ["property.mouza", "financial.unreferenced_field"],
    }
    docx_bytes = create_minimal_docx_bytes(body)

    linter = DocxLinter()
    report = linter.lint(docx_bytes, manifest=manifest)

    # Undefined tag is an error and blocks approval
    assert any(e.code == "UNDEFINED_TAG" and "undefined_secret_tag" in e.message for e in report.errors)
    assert report.can_approve is False

    # Unreferenced field is a warning
    assert any(w.code == "UNUSED_FIELD" and "financial.unreferenced_field" in w.message for w in report.warnings)


def test_sale_deed_plot_mr_template_lint_clean() -> None:
    """Verifies that approved sale_deed_plot_mr template passes lint cleanly."""
    template_path = Path(__file__).parent.parent.parent.parent / "templates-library" / "sale_deed_plot_mr" / "template.docx"
    manifest_path = Path(__file__).parent.parent.parent.parent / "templates-library" / "sale_deed_plot_mr" / "manifest.json"

    assert template_path.exists()
    assert manifest_path.exists()

    docx_bytes = template_path.read_bytes()
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

    linter = DocxLinter()
    report = linter.lint(docx_bytes, manifest=manifest_data)

    # Must be free of leftover data and approval-blocking errors
    assert len(report.leftover_data) == 0, f"Leftover data found in approved template: {report.leftover_data}"
    assert len(report.errors) == 0, f"Errors found in approved template: {report.errors}"
    assert report.can_approve is True

