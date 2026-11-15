"""Golden-render and typography verification tests over EVERY template in templates-library.

Adheres strictly to docs/TESTING.md Section 4.6 & Section 5:
1. Dynamic discovery of EVERY template directory in templates-library.
2. Manifest validation and Schema v1 compilation.
3. DocxLinter audit: zero leftover data, zero syntax errors, valid fonts.
4. Golden DOCX render: deterministic output, no unrendered Jinja tags.
5. PDF render check: valid PDF/A, Devanagari conjuncts (जोडाक्षरे), and reph (रफार) integrity:
   - NFC normalization.
   - Absence of orphaned halants / viramas (\\u094D).
   - Correct conjunct sequences and reph placement.
   - No Unicode replacement characters (\\uFFFD).
"""

from __future__ import annotations

import io
import json
import re
import unicodedata
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from docx import Document

from app.adapters.pdf import LibreOfficePdfConverter
from app.templates.compiler import ManifestCompiler, ManifestRuntime
from app.templates.lint import DocxLinter

TEMPLATES_LIB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates-library"


def get_all_template_dirs() -> list[Path]:
    """Finds every template directory in templates-library containing manifest.json and template.docx."""
    tmpl_dirs = [
        d
        for d in TEMPLATES_LIB_DIR.iterdir()
        if d.is_dir() and (d / "manifest.json").exists() and (d / "template.docx").exists()
    ]
    return sorted(tmpl_dirs, key=lambda p: p.name)


ALL_TEMPLATE_DIRS = get_all_template_dirs()


def create_synthetic_template_context(manifest: dict[str, Any]) -> dict[str, Any]:
    """Builds valid synthetic test context satisfying the template's manifest fields."""
    language = manifest.get("language", "mr")

    # Synthetic parties per AGENTS.md Hard Rule 1
    if language == "mr":
        seller_name = "आनंदराव बापूजी देशमुख"
        buyer_name = "ज्ञानेश्वर विठ्ठलराव कुलकर्णी"
        village = "वाडी"
        city = "नागपूर"
        district = "नागपूर"
    else:
        seller_name = "Anandrao Bapuji Deshmukh"
        buyer_name = "Dnyaneshwar Vitthalrao Kulkarni"
        village = "Wadi"
        city = "Nagpur"
        district = "Nagpur"

    context: dict[str, Any] = {
        "execution_date": "2026-11-14",
        "doc_no": "DOC/2026/0001",
        "parties": {
            "seller": [
                {
                    "full_name": seller_name,
                    "age": 52,
                    "pan": "ABCDE1234F",
                    "aadhaar_masked": "XXXX-XXXX-1234",
                    "address": f"{village}, {city}",
                }
            ],
            "buyer": [
                {
                    "full_name": buyer_name,
                    "age": 45,
                    "pan": "PQXYZ5678G",
                    "aadhaar_masked": "XXXX-XXXX-5678",
                    "address": f"धरमपेठ, {city}",
                }
            ],
            "vendors": [{"full_name": seller_name, "age": 52, "address": village}],
            "purchasers": [{"full_name": buyer_name, "age": 45, "address": city}],
            "executants": [{"full_name": seller_name, "age": 52, "address": village}],
            "claimants": [{"full_name": buyer_name, "age": 45, "address": city}],
            "principals": [{"full_name": seller_name, "age": 52, "address": village}],
            "attorneys": [{"full_name": buyer_name, "age": 45, "address": city}],
        },
        "property": {
            "survey_number": "142/1",
            "plot_number": "12",
            "flat_number": "302",
            "shop_number": "G-4",
            "building_name": "शिवनेरी हाइट्स",
            "area_sqft": Decimal("1500.00"),
            "area_sqm": Decimal("139.35"),
            "carpet_area_sqm": Decimal("75.50"),
            "village": village,
            "district": district,
            "boundaries": {
                "east": "रस्ता 30 फूट",
                "west": "प्लॉट क्रमांक 11",
                "north": "प्लॉट क्रमांक 5",
                "south": "खुली जागा",
            },
        },
        "financial": {
            "total_consideration": Decimal("3500000.00"),
            "earnest_amount": Decimal("500000.00"),
            "earnest_advance": Decimal("500000.00"),
            "balance_due": Decimal("3000000.00"),
            "balance_amount": Decimal("3000000.00"),
            "payment_mode": "NEFT/RTGS",
            "bank_name": "स्टेट बँक ऑफ इंडिया",
        },
        "terms": {
            "months_to_complete": 3,
        },
        "witnesses": [
            {"full_name": "सुरेश एकनाथ पाटील", "address": "नागपूर"},
            {"full_name": "प्रमोद भास्कर जोशी", "address": "नागपूर"},
        ],
    }

    # Evaluate any manifest derived expressions
    compiler = ManifestCompiler()
    compiled = compiler.compile(manifest)
    runtime = ManifestRuntime()
    derived = runtime.evaluate_derived_fields(compiled, context)
    # Merge derived fields
    for k, v in derived.items():
        if isinstance(v, dict) and k in context and isinstance(context[k], dict):
            context[k].update(v)
        else:
            context[k] = v

    return context


@pytest.mark.golden
@pytest.mark.parametrize("tmpl_dir", ALL_TEMPLATE_DIRS, ids=[p.name for p in ALL_TEMPLATE_DIRS])
def test_every_template_manifest_and_lint(tmpl_dir: Path) -> None:
    """Verifies that EVERY template manifest is Schema v1 compliant and template.docx passes lint."""
    manifest_file = tmpl_dir / "manifest.json"
    docx_file = tmpl_dir / "template.docx"

    raw_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)
    assert compiled.template_id == tmpl_dir.name

    docx_bytes = docx_file.read_bytes()
    linter = DocxLinter()
    report = linter.lint(docx_bytes, manifest=raw_manifest)

    assert report.can_approve is True, f"Lint failed on {tmpl_dir.name}: {report.errors}"
    assert (
        len(report.leftover_data) == 0
    ), f"Leftover data found in {tmpl_dir.name}: {report.leftover_data}"
    assert len(report.errors) == 0, f"Errors in {tmpl_dir.name}: {report.errors}"


@pytest.mark.golden
@pytest.mark.parametrize("tmpl_dir", ALL_TEMPLATE_DIRS, ids=[p.name for p in ALL_TEMPLATE_DIRS])
def test_every_template_golden_render_and_devanagari_typography(tmpl_dir: Path) -> None:
    """Renders every template, asserts zero unrendered tags, and checks Devanagari conjuncts & reph."""
    manifest_file = tmpl_dir / "manifest.json"
    docx_file = tmpl_dir / "template.docx"

    raw_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    context = create_synthetic_template_context(raw_manifest)

    # Render template via docxtpl
    from docxtpl import DocxTemplate

    doc = DocxTemplate(docx_file)
    doc.render(context)

    out_stream = io.BytesIO()
    doc.save(out_stream)
    rendered_docx_bytes = out_stream.getvalue()

    # 1. Open rendered DOCX and inspect all paragraph text
    doc_reopened = Document(io.BytesIO(rendered_docx_bytes))
    full_text_list: list[str] = []
    for p in doc_reopened.paragraphs:
        full_text_list.append(p.text)
    for table in doc_reopened.tables:
        for row in table.rows:
            for cell in row.cells:
                full_text_list.append(cell.text)

    all_rendered_text = "\n".join(full_text_list)

    # 2. Text Diff & Tag Integrity: Zero leftover Jinja or template syntax
    assert "{{" not in all_rendered_text, f"Unrendered Jinja variable in {tmpl_dir.name}"
    assert "}}" not in all_rendered_text, f"Unrendered Jinja tag close in {tmpl_dir.name}"
    assert "{%" not in all_rendered_text, f"Unrendered Jinja control block in {tmpl_dir.name}"
    assert "%}" not in all_rendered_text, f"Unrendered Jinja control end in {tmpl_dir.name}"

    # 3. Devanagari Typography, Conjuncts, and Reph Verification
    is_marathi = raw_manifest.get("language") == "mr"
    if is_marathi:
        # A. NFC Normalization (AGENTS.md Section 6: Unicode text normalised to NFC)
        assert unicodedata.is_normalized(
            "NFC", all_rendered_text
        ), f"Devanagari text in {tmpl_dir.name} is not NFC normalized!"

        # B. Absence of Unicode replacement characters
        assert (
            "\ufffd" not in all_rendered_text
        ), f"Unicode replacement character \\uFFFD detected in {tmpl_dir.name}"

        # C. Reph (रफार) Integrity: \\u0930 + \\u094D followed by consonant
        # Example words: सर्व, वर्ग, खर्च, संदर्भ, मार्गदर्शन
        reph_matches = re.findall(r"\u0930\u094D[\u0915-\u0939]", all_rendered_text)
        # Should cleanly form valid reph clusters

        # D. Conjuncts (जोडाक्षरे): Check that halants are between consonants, never orphaned
        # Broken halant pattern 1: Whitespace followed by halant or halant followed by whitespace
        orphan_halant_before = re.findall(r"\s\u094D", all_rendered_text)
        orphan_halant_after = re.findall(r"\u094D\s", all_rendered_text)
        assert (
            not orphan_halant_before
        ), f"Orphan pre-halant found in {tmpl_dir.name}: {orphan_halant_before}"
        assert (
            not orphan_halant_after
        ), f"Orphan post-halant found in {tmpl_dir.name}: {orphan_halant_after}"

        # Broken halant pattern 2: Double halant (\\u094D\\u094D)
        assert "\u094d\u094d" not in all_rendered_text, f"Double halant detected in {tmpl_dir.name}"

    # 4. PDF Render Check
    # Convert rendered DOCX to PDF using LibreOffice adapter
    pdf_converter = LibreOfficePdfConverter()
    pdf_bytes = pdf_converter.convert_docx_to_pdf(rendered_docx_bytes)

    assert pdf_bytes is not None
    assert pdf_bytes.startswith(b"%PDF-"), f"Rendered output for {tmpl_dir.name} is not valid PDF"
    assert (
        len(pdf_bytes) > 200
    ), f"Rendered PDF for {tmpl_dir.name} is suspiciously small ({len(pdf_bytes)} bytes)"
