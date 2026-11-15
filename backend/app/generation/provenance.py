"""Document provenance and tamper-evident cryptographic stamping (custom XML part).

Adheres strictly to docs/ARCHITECTURE.md Section 7 & PRD G4:
- Stamped inside DOCX as a custom XML package part (customXml/provenance.xml).
- Never visible in document body text.
- Carries template_version_id, template_sha256, engine_version, document_hash (SHA-256 of word/document.xml), and timestamp.
- Allows deterministic tamper verification by recomputing word/document.xml hash and comparing.
"""

from __future__ import annotations

import datetime
import hashlib
import io
import uuid
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass

import defusedxml.ElementTree as SafeET
from defusedxml.common import DefusedXmlException

PROVENANCE_XML_PATH = "customXml/provenance.xml"
PROVENANCE_XML_NS = "http://schemas.lekhan.local/provenance/v1"


@dataclass
class ProvenanceRecord:
    document_id: str
    tenant_id: str
    template_version_id: str
    template_sha256: str
    engine_version: str
    document_hash: str
    generated_at: str


@dataclass
class ProvenanceVerificationResult:
    valid: bool
    tampered: bool
    document_id: str | None = None
    tenant_id: str | None = None
    template_version_id: str | None = None
    template_sha256: str | None = None
    engine_version: str | None = None
    expected_document_hash: str | None = None
    actual_document_hash: str | None = None
    generated_at: str | None = None
    verified_at: str = ""
    message: str = ""


def stamp_docx_provenance(
    docx_bytes: bytes,
    document_id: uuid.UUID | str,
    tenant_id: uuid.UUID | str,
    template_version_id: uuid.UUID | str,
    template_sha256: str,
    engine_version: str = "1.0.0",
    generated_at: datetime.datetime | None = None,
) -> bytes:
    """Injects a tamper-evident custom XML provenance part into the OpenXML DOCX archive."""
    now_iso = (generated_at or datetime.datetime.now(datetime.timezone.utc)).isoformat()

    in_zip = zipfile.ZipFile(io.BytesIO(docx_bytes), "r")
    files: dict[str, bytes] = {
        item.filename: in_zip.read(item.filename) for item in in_zip.infolist()
    }
    in_zip.close()

    # 1. Compute document_hash from word/document.xml
    doc_xml_bytes = files.get("word/document.xml")
    if not doc_xml_bytes:
        raise ValueError("Invalid DOCX: missing word/document.xml")

    document_hash = hashlib.sha256(doc_xml_bytes).hexdigest()

    # 2. Build provenance XML document
    root = ET.Element(f"{{{PROVENANCE_XML_NS}}}provenance")
    ET.SubElement(root, f"{{{PROVENANCE_XML_NS}}}documentId").text = str(document_id)
    ET.SubElement(root, f"{{{PROVENANCE_XML_NS}}}tenantId").text = str(tenant_id)
    ET.SubElement(root, f"{{{PROVENANCE_XML_NS}}}templateVersionId").text = str(template_version_id)
    ET.SubElement(root, f"{{{PROVENANCE_XML_NS}}}templateSha256").text = str(template_sha256)
    ET.SubElement(root, f"{{{PROVENANCE_XML_NS}}}engineVersion").text = str(engine_version)
    ET.SubElement(root, f"{{{PROVENANCE_XML_NS}}}documentHash").text = str(document_hash)
    ET.SubElement(root, f"{{{PROVENANCE_XML_NS}}}generatedAt").text = str(now_iso)

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    # 3. Add to files map
    files[PROVENANCE_XML_PATH] = xml_bytes

    # 4. Rebuild DOCX ZIP with custom XML part
    out_buf = io.BytesIO()
    with zipfile.ZipFile(out_buf, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
        for fname, content in files.items():
            out_zip.writestr(fname, content)

    return out_buf.getvalue()


def extract_docx_provenance(docx_bytes: bytes) -> ProvenanceRecord | None:
    """Extracts the provenance custom XML part from a DOCX file, if present."""
    try:
        with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
            if PROVENANCE_XML_PATH not in zf.namelist():
                return None
            xml_bytes = zf.read(PROVENANCE_XML_PATH)

        try:
            root = SafeET.fromstring(
                xml_bytes,
                forbid_dtd=True,
                forbid_entities=True,
                forbid_external=True,
            )
        except (DefusedXmlException, SafeET.ParseError):
            return None
        ns = {"p": PROVENANCE_XML_NS}

        def _get_val(tag: str) -> str:
            elem = root.find(f"p:{tag}", ns)
            return elem.text if elem is not None and elem.text else ""

        return ProvenanceRecord(
            document_id=_get_val("documentId"),
            tenant_id=_get_val("tenantId"),
            template_version_id=_get_val("templateVersionId"),
            template_sha256=_get_val("templateSha256"),
            engine_version=_get_val("engineVersion"),
            document_hash=_get_val("documentHash"),
            generated_at=_get_val("generatedAt"),
        )
    except Exception:
        return None


def verify_docx_provenance(docx_bytes: bytes) -> ProvenanceVerificationResult:
    """Recomputes the hash of word/document.xml and compares against the provenance XML stamp."""
    verified_at_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    try:
        with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
            # 1. Read word/document.xml
            if "word/document.xml" not in zf.namelist():
                return ProvenanceVerificationResult(
                    valid=False,
                    tampered=True,
                    verified_at=verified_at_iso,
                    message="Corrupted DOCX archive: word/document.xml is missing.",
                )
            doc_xml_bytes = zf.read("word/document.xml")
            actual_doc_hash = hashlib.sha256(doc_xml_bytes).hexdigest()

            # 2. Read customXml/provenance.xml
            if PROVENANCE_XML_PATH not in zf.namelist():
                return ProvenanceVerificationResult(
                    valid=False,
                    tampered=False,
                    actual_document_hash=actual_doc_hash,
                    verified_at=verified_at_iso,
                    message="Document lacks provenance stamp (customXml/provenance.xml missing).",
                )
            prov_xml_bytes = zf.read(PROVENANCE_XML_PATH)

        try:
            root = SafeET.fromstring(
                prov_xml_bytes,
                forbid_dtd=True,
                forbid_entities=True,
                forbid_external=True,
            )
        except (DefusedXmlException, SafeET.ParseError) as exc:
            return ProvenanceVerificationResult(
                valid=False,
                tampered=True,
                actual_document_hash=actual_doc_hash,
                verified_at=verified_at_iso,
                message=f"Malicious or malformed provenance XML rejected: {exc}",
            )
        ns = {"p": PROVENANCE_XML_NS}

        def _get(tag: str) -> str:
            el = root.find(f"p:{tag}", ns)
            return el.text if el is not None and el.text else ""

        expected_doc_hash = _get("documentHash")
        is_tampered = actual_doc_hash != expected_doc_hash

        return ProvenanceVerificationResult(
            valid=not is_tampered,
            tampered=is_tampered,
            document_id=_get("documentId"),
            tenant_id=_get("tenantId"),
            template_version_id=_get("templateVersionId"),
            template_sha256=_get("templateSha256"),
            engine_version=_get("engineVersion"),
            expected_document_hash=expected_doc_hash,
            actual_document_hash=actual_doc_hash,
            generated_at=_get("generatedAt"),
            verified_at=verified_at_iso,
            message=(
                "Cryptographic provenance verified: document content is authentic and untampered."
                if not is_tampered
                else "Tamper alert: word/document.xml SHA-256 hash does not match provenance stamp!"
            ),
        )
    except Exception as exc:
        return ProvenanceVerificationResult(
            valid=False,
            tampered=True,
            verified_at=verified_at_iso,
            message=f"Verification failed with archive error: {type(exc).__name__}",
        )
