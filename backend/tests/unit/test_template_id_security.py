"""Security tests for template_id and LocalObjectStore path traversal protection.

Verifies protection against:
- Directory traversal (../)
- Absolute paths
- URL-encoded traversal (%2e%2e)
- NUL byte injection
- Symlink resolution escaping base root
- Sibling-prefix directory collision
Each attack vector MUST return 400/404 and write nothing to disk.
"""

from __future__ import annotations

import io
import json
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.adapters.storage import LocalObjectStore
from app.api.auth import get_current_actor, require_csrf
from app.identity.policy import Actor
from app.main import app
from app.templates.validator import TEMPLATES_DIR, validate_template_id

client = TestClient(app)

TEMPLATE_ADMIN_ACTOR = Actor(
    user_id=uuid.uuid4(),
    tenant_id=uuid.uuid4(),
    role="template_admin",
)

TRAVERSAL_PAYLOADS = [
    "../escape",
    "../../etc/passwd",
    "..\\escape",
    "/etc/passwd",
    "C:/Windows/System32",
    "C:\\Windows\\System32",
    "%2e%2e/escape",
    "%2e%2e%2fescape",
    "tmpl\0escape",
    "tmpl%00escape",
    "templates-library-sibling",
    "../templates-library-sibling",
    "a",  # too short (< 3 chars)
    "a" * 65,  # too long (> 64 chars)
    "invalid-char!",
    "has space",
]


@pytest.fixture(autouse=True)
def override_actor():
    app.dependency_overrides[get_current_actor] = lambda: TEMPLATE_ADMIN_ACTOR
    app.dependency_overrides[require_csrf] = lambda: None
    yield
    app.dependency_overrides.pop(get_current_actor, None)
    app.dependency_overrides.pop(require_csrf, None)


# ---------------------------------------------------------------------------
# 1. Unit Tests for validate_template_id()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("payload", TRAVERSAL_PAYLOADS)
def test_validate_template_id_rejects_malicious_inputs(payload: str) -> None:
    """Verifies validate_template_id raises ValueError on traversal or invalid IDs."""
    with pytest.raises(ValueError):
        validate_template_id(payload)


def test_validate_template_id_valid() -> None:
    """Verifies that legitimate template IDs pass validation and return resolved Path."""
    valid_id = "sale_deed_plot_mr"
    resolved = validate_template_id(valid_id)
    assert resolved == (TEMPLATES_DIR / valid_id).resolve()
    assert resolved.is_relative_to(TEMPLATES_DIR)


def test_validate_template_id_symlink(tmp_path: Path) -> None:
    """Verifies that symlinks are strictly rejected even if pointing inside or outside."""
    symlink_path = tmp_path / "sym_tmpl"
    try:
        symlink_path.symlink_to(tmp_path.parent)
        with pytest.raises(ValueError, match="Symlinks prohibited"):
            validate_template_id("sym_tmpl", base_dir=tmp_path)
    except OSError:
        # Fallback for Windows environments without SeCreateSymbolicLinkPrivilege
        with patch.object(Path, "is_symlink", return_value=True):
            with pytest.raises(ValueError, match="Symlinks prohibited"):
                validate_template_id("sym_tmpl", base_dir=tmp_path)


def test_validate_template_id_sibling_prefix(tmp_path: Path) -> None:
    """Verifies that sibling directories with shared prefix are rejected."""
    base_dir = tmp_path / "templates"
    base_dir.mkdir(parents=True, exist_ok=True)
    sibling_evil = tmp_path / "templates_evil"
    sibling_evil.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError):
        validate_template_id("../templates_evil", base_dir=base_dir)


# ---------------------------------------------------------------------------
# 2. Unit Tests for LocalObjectStore._resolve_path()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key",
    [
        "../escape.docx",
        "../../etc/passwd",
        "/etc/shadow",
        "C:/Windows/System32",
        "%2e%2e/escape.docx",
        "%2e%2e%2fescape.docx",
        "file\0escape.docx",
        "file%00escape.docx",
    ],
)
def test_local_object_store_resolve_path_rejects_traversal(tmp_path: Path, key: str) -> None:
    """Verifies LocalObjectStore rejects directory traversal and escapes."""
    store = LocalObjectStore(base_path=tmp_path)
    with pytest.raises(ValueError):
        store._resolve_path(key)


def test_local_object_store_sibling_prefix_rejected(tmp_path: Path) -> None:
    """Verifies is_relative_to prevents sibling prefix collision in storage."""
    base_store = tmp_path / "storage"
    base_store.mkdir(parents=True, exist_ok=True)
    sibling_store = tmp_path / "storage_backup"
    sibling_store.mkdir(parents=True, exist_ok=True)

    store = LocalObjectStore(base_path=base_store)
    with pytest.raises(ValueError):
        store._resolve_path("../storage_backup/secret.txt")


def test_local_object_store_put_writes_nothing_on_traversal(tmp_path: Path) -> None:
    """Verifies store.put() with traversal keys raises ValueError and writes zero bytes."""
    store = LocalObjectStore(base_path=tmp_path)
    initial_files = list(tmp_path.rglob("*"))

    with pytest.raises(ValueError):
        store.put("../traversal_write.txt", b"MALICIOUS_PAYLOAD")

    # Verify no new files written anywhere
    current_files = list(tmp_path.rglob("*"))
    assert current_files == initial_files
    assert not (tmp_path.parent / "traversal_write.txt").exists()


# ---------------------------------------------------------------------------
# 3. HTTP API Endpoint Tests: 400/404 & Zero Disk Writes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "malicious_id",
    [
        "../traversal_upload",
        "/etc/passwd",
        "%2e%2e/traversal",
        "test\0upload",
        "templates-library-evil",
    ],
)
def test_upload_template_rejects_traversal_and_writes_nothing(
    tmp_path: Path, malicious_id: str
) -> None:
    """Verifies POST /api/v1/templates/upload returns 400 and writes nothing on traversal."""
    dummy_docx = io.BytesIO(b"PK\x03\x04" + b"\x00" * 30)

    res = client.post(
        "/api/v1/templates/upload",
        data={
            "template_id": malicious_id,
            "manifest_json": json.dumps({"name": "Evil Template"}),
        },
        files={
            "docx_file": (
                "template.docx",
                dummy_docx,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert res.status_code in (400, 404, 422)
    # Verify nothing was written to templates-library or parent
    assert not (TEMPLATES_DIR / malicious_id).exists()
    assert not (TEMPLATES_DIR.parent / "traversal_upload").exists()


@pytest.mark.parametrize(
    "malicious_id",
    ["../evil", "%2e%2e", "/etc/passwd", "tmpl\0bad"],
)
def test_template_routes_reject_traversal(malicious_id: str) -> None:
    """Verifies all template endpoints return 400 or 404 on traversal template_id."""
    # 1. Manifest
    res = client.get(f"/api/v1/templates/{malicious_id}/manifest")
    assert res.status_code in (400, 404)

    # 2. Lint
    res = client.post(f"/api/v1/templates/{malicious_id}/lint")
    assert res.status_code in (400, 404)

    # 3. Submit
    res = client.post(f"/api/v1/templates/{malicious_id}/submit")
    assert res.status_code in (400, 404)

    # 4. Approve
    res = client.post(f"/api/v1/templates/{malicious_id}/approve")
    assert res.status_code in (400, 404)

    # 5. Retire
    res = client.post(f"/api/v1/templates/{malicious_id}/retire")
    assert res.status_code in (400, 404)

    # 6. /documents/validate/{id}
    res = client.post(
        f"/api/v1/documents/validate/{malicious_id}",
        json={"data": {}},
    )
    assert res.status_code in (400, 404)
