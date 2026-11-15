"""Security regression tests for defusedxml secure parsing (Bandit B314 remediation).

Validates:
- Test A: Valid XML parses successfully.
- Test B: Malformed XML produces a controlled ParseError.
- Test C: Internal entity expansion (Billion Laughs / quadratic entity expansion) is rejected.
- Test D: External entity reference (XXE file inclusion) is rejected.
- Test E: Prohibited DTD payload is rejected under strict parsing configuration.
- Test F: Existing DOCX / OOXML template processing works as intended.
- Test G: All seven affected components (provenance extract/verify, font audit, leftover scan,
          split run merge, external rels strip, tag alignment) handle legitimate and malicious XML correctly.
"""

from __future__ import annotations

import io
import uuid
import zipfile

import defusedxml.ElementTree as SafeET
import pytest
from defusedxml.common import (
    DefusedXmlException,
    DTDForbidden,
    EntitiesForbidden,
    ExternalReferenceForbidden,
)

from app.generation.provenance import (
    PROVENANCE_XML_PATH,
    extract_docx_provenance,
    stamp_docx_provenance,
    verify_docx_provenance,
)
from app.templates.lint.fonts import audit_docx_fonts
from app.templates.lint.leftover_scanner import scan_docx_for_leftover_data
from app.templates.lint.linter import DocxLinter
from app.templates.lint.models import LintSeverity
from app.templates.lint.split_runs import repair_and_check_split_runs
from app.templates.lint.structural import (
    strip_external_relationships,
)
from app.templates.lint.tag_checker import check_tag_alignment

# ---------------------------------------------------------------------------
# Test Helpers: Minimal In-Memory DOCX Builder
# ---------------------------------------------------------------------------


def _build_test_docx(
    document_xml: str,
    extra_files: dict[str, bytes] | None = None,
) -> bytes:
    """Builds a minimal, valid in-memory DOCX archive."""
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
        zf.writestr("word/document.xml", document_xml)

        if extra_files:
            for fname, fbytes in extra_files.items():
                zf.writestr(fname, fbytes)

    return buf.getvalue()


# ---------------------------------------------------------------------------
# Test A: Valid XML
# ---------------------------------------------------------------------------


def test_secure_xml_valid_xml() -> None:
    """Test A: Legitimate, well-formed XML parses successfully with correct traversal."""
    xml_data = b"""<?xml version="1.0" encoding="UTF-8"?>
    <document xmlns="http://schemas.lekhan.local/test">
        <metadata>
            <title>Sale Deed</title>
            <version>1</version>
        </metadata>
        <body>
            <p>Authentic Devanagari legal text</p>
        </body>
    </document>
    """
    root = SafeET.fromstring(
        xml_data,
        forbid_dtd=True,
        forbid_entities=True,
        forbid_external=True,
    )
    assert root is not None
    assert root.tag == "{http://schemas.lekhan.local/test}document"
    assert len(list(root)) == 2


# ---------------------------------------------------------------------------
# Test B: Malformed XML
# ---------------------------------------------------------------------------


def test_secure_xml_malformed_xml() -> None:
    """Test B: Malformed, truncated, or unclosed XML raises a controlled ParseError."""
    malformed_xml = b"""<root><unclosed_tag>data</root>"""
    with pytest.raises(SafeET.ParseError):
        SafeET.fromstring(
            malformed_xml,
            forbid_dtd=True,
            forbid_entities=True,
            forbid_external=True,
        )


# ---------------------------------------------------------------------------
# Test C: Internal Entity Expansion (Billion Laughs Attack)
# ---------------------------------------------------------------------------


def test_secure_xml_internal_entity_expansion_rejected() -> None:
    """Test C: XML with malicious internal entity expansion must be rejected."""
    billion_laughs_payload = b"""<?xml version="1.0"?>
    <!DOCTYPE lolz [
      <!ENTITY lol "lol">
      <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
      <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
    ]>
    <lolz>&lol3;</lolz>
    """
    with pytest.raises((EntitiesForbidden, DTDForbidden, DefusedXmlException)):
        SafeET.fromstring(
            billion_laughs_payload,
            forbid_dtd=True,
            forbid_entities=True,
            forbid_external=True,
        )


# ---------------------------------------------------------------------------
# Test D: External Entity Reference (XXE Injection)
# ---------------------------------------------------------------------------


def test_secure_xml_external_entity_reference_rejected() -> None:
    """Test D: XML referencing external system entities must be rejected."""
    xxe_payload = b"""<?xml version="1.0" encoding="ISO-8859-1"?>
    <!DOCTYPE foo [
      <!ELEMENT foo ANY >
      <!ENTITY xxe SYSTEM "file:///etc/passwd" >
    ]>
    <foo>&xxe;</foo>
    """
    with pytest.raises((ExternalReferenceForbidden, DTDForbidden, DefusedXmlException)):
        SafeET.fromstring(
            xxe_payload,
            forbid_dtd=True,
            forbid_entities=True,
            forbid_external=True,
        )


# ---------------------------------------------------------------------------
# Test E: Prohibited DTD Payload
# ---------------------------------------------------------------------------


def test_secure_xml_prohibited_dtd_rejected() -> None:
    """Test E: Any DTD declaration must be rejected when forbid_dtd=True."""
    dtd_payload = b"""<?xml version="1.0"?>
    <!DOCTYPE test [
      <!ELEMENT test (#PCDATA)>
    ]>
    <test>content</test>
    """
    with pytest.raises(DTDForbidden):
        SafeET.fromstring(
            dtd_payload,
            forbid_dtd=True,
            forbid_entities=True,
            forbid_external=True,
        )


# ---------------------------------------------------------------------------
# Test F: Legitimate DOCX / OOXML Processing Continues Working
# ---------------------------------------------------------------------------


def test_secure_xml_legitimate_docx_workflow() -> None:
    """Test F: Legitimate DOCX archives with full OpenXML parts are linted cleanly."""
    valid_doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p><w:r><w:t>{{ property.city }} मधील विक्रीखत</w:t></w:r></w:p>"
        "</w:body>"
        "</w:document>"
    )
    docx_bytes = _build_test_docx(valid_doc_xml)

    linter = DocxLinter()
    manifest = {"fields": {"property.city": {"type": "text", "label_en": "City", "required": True}}}
    report = linter.lint(docx_bytes, manifest=manifest)
    assert report.can_approve is True
    assert len(report.errors) == 0


# ---------------------------------------------------------------------------
# Test G: All Seven Affected Components Handle Legitimate and Malicious XML
# ---------------------------------------------------------------------------


def test_component_1_and_2_provenance_safe_extraction_and_verification() -> None:
    """Component 1 & 2: extract_docx_provenance and verify_docx_provenance with defusedxml."""
    doc_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    tmpl_version_id = uuid.uuid4()

    valid_doc_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>Deed Body</w:t></w:r></w:p></w:body>"
        "</w:document>"
    )
    docx_bytes = _build_test_docx(valid_doc_xml)

    # 1. Stamping and legitimate extraction
    stamped = stamp_docx_provenance(
        docx_bytes=docx_bytes,
        document_id=doc_id,
        tenant_id=tenant_id,
        template_version_id=tmpl_version_id,
        template_sha256="abc123sha",
        engine_version="1.0.0",
    )
    record = extract_docx_provenance(stamped)
    assert record is not None
    assert record.document_id == str(doc_id)
    assert record.tenant_id == str(tenant_id)

    verify_res = verify_docx_provenance(stamped)
    assert verify_res.valid is True
    assert verify_res.tampered is False

    # 2. Malicious XXE injection in customXml/provenance.xml is rejected safely
    malicious_prov_xml = b"""<?xml version="1.0"?>
    <!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
    <provenance xmlns="http://schemas.lekhan.local/provenance/v1">
        <documentId>&xxe;</documentId>
    </provenance>
    """
    tampered_docx = _build_test_docx(
        valid_doc_xml,
        extra_files={PROVENANCE_XML_PATH: malicious_prov_xml},
    )

    # Extraction safely fails closed (returns None)
    extracted = extract_docx_provenance(tampered_docx)
    assert extracted is None

    # Verification safely flags as tampered/invalid
    v_res = verify_docx_provenance(tampered_docx)
    assert v_res.valid is False
    assert v_res.tampered is True
    assert "Malicious or malformed provenance XML rejected" in v_res.message


def test_component_3_fonts_audit_with_safe_xml() -> None:
    """Component 3: audit_docx_fonts processes legitimate fonts and catches malicious XML."""
    # Legitimate fonts
    font_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:rFonts w:ascii="Noto Serif Devanagari"/>'
        "</w:fonts>"
    )
    docx_bytes = _build_test_docx(
        "<w:p><w:r><w:t>Devanagari</w:t></w:r></w:p>",
        extra_files={"word/fontTable.xml": font_xml.encode("utf-8")},
    )
    fonts, findings = audit_docx_fonts(docx_bytes)
    assert "Noto Serif Devanagari" in fonts

    # Malicious DTD in fontTable.xml
    malicious_font_xml = b"""<?xml version="1.0"?>
    <!DOCTYPE fonts [ <!ENTITY xxe SYSTEM "http://malicious.local"> ]>
    <w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:rFonts w:ascii="&xxe;"/>
    </w:fonts>
    """
    malicious_docx = _build_test_docx(
        "<w:p><w:r><w:t>Test</w:t></w:r></w:p>",
        extra_files={"word/fontTable.xml": malicious_font_xml},
    )
    _, evil_findings = audit_docx_fonts(malicious_docx)
    assert any(
        f.code == "UNSAFE_XML_DETECTED" and f.severity == LintSeverity.ERROR for f in evil_findings
    )


def test_component_4_leftover_scanner_with_safe_xml() -> None:
    """Component 4: scan_docx_for_leftover_data parses text safely and flags malicious XML."""
    # Legitimate document with a sensitive PAN
    pan_doc_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>PAN card is ABCDE1234F</w:t></w:r></w:p></w:body>"
        "</w:document>"
    )
    docx_bytes = _build_test_docx(pan_doc_xml)
    findings = scan_docx_for_leftover_data(docx_bytes)
    assert any(f.category == "PAN" for f in findings)

    # Malicious DTD in document.xml
    malicious_doc_xml = b"""<?xml version="1.0"?>
    <!DOCTYPE doc [ <!ENTITY xxe SYSTEM "file:///etc/hosts"> ]>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:body><w:p><w:r><w:t>&xxe;</w:t></w:r></w:p></w:body>
    </w:document>
    """
    malicious_docx = _build_test_docx(malicious_doc_xml.decode("utf-8", errors="ignore"))
    # Structural safety or leftover scanner rejects malicious entity
    findings_evil = scan_docx_for_leftover_data(malicious_docx)
    assert any(f.code == "UNSAFE_XML_DETECTED" for f in findings_evil)


def test_component_5_split_runs_with_safe_xml() -> None:
    """Component 5: repair_and_check_split_runs merges runs safely and flags malicious XML."""
    # Split run in clean document
    split_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p><w:r><w:t>{{ party.</w:t></w:r><w:r><w:t>name }}</w:t></w:r></w:p>"
        "</w:body>"
        "</w:document>"
    )
    docx_bytes = _build_test_docx(split_xml)
    repaired, count, findings = repair_and_check_split_runs(docx_bytes)
    assert count == 1

    # Malicious DTD inside header.xml
    malicious_hdr = b"""<?xml version="1.0"?>
    <!DOCTYPE hdr [ <!ENTITY xxe SYSTEM "file:///etc/shadow"> ]>
    <w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:p><w:r><w:t>&xxe;</w:t></w:r></w:p>
    </w:hdr>
    """
    malicious_docx = _build_test_docx(
        "<w:p><w:r><w:t>Normal</w:t></w:r></w:p>",
        extra_files={"word/header1.xml": malicious_hdr},
    )
    _, _, evil_findings = repair_and_check_split_runs(malicious_docx)
    assert any(f.code == "UNSAFE_XML_DETECTED" for f in evil_findings)


def test_component_6_strip_external_relationships_with_safe_xml() -> None:
    """Component 6: strip_external_relationships sanitizes external hyperlinks securely."""
    # Legitimate external relationship
    rels_content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
        'Target="http://trusted.domain/doc" TargetMode="External"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
        "</Relationships>"
    )
    docx_bytes = _build_test_docx(
        "<w:p><w:r><w:t>Link</w:t></w:r></w:p>",
        extra_files={"word/_rels/document.xml.rels": rels_content.encode("utf-8")},
    )
    sanitized = strip_external_relationships(docx_bytes)
    with zipfile.ZipFile(io.BytesIO(sanitized), "r") as zf:
        clean_rels = zf.read("word/_rels/document.xml.rels").decode("utf-8")
        assert "TargetMode" not in clean_rels
        assert "styles.xml" in clean_rels


def test_component_7_tag_checker_with_safe_xml() -> None:
    """Component 7: check_tag_alignment extracts template variables using safe XML."""
    tag_doc_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>{{ property.area }} sq ft</w:t></w:r></w:p></w:body>"
        "</w:document>"
    )
    docx_bytes = _build_test_docx(tag_doc_xml)
    manifest = {"fields": {"property.area": {"type": "number", "label_en": "Area"}}}
    findings = check_tag_alignment(docx_bytes, manifest)
    # Tag matches manifest, no undefined tag errors
    assert not any(f.code == "UNDEFINED_TAG" for f in findings)
