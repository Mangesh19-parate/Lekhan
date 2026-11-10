"""Unit tests for Template Registry and immutable version guarantees."""

import uuid
import pytest

from app.adapters.storage import LocalObjectStore
from app.templates.registry import TemplateImmutabilityError, TemplateRegistry

SUBMITTER_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
REVIEWER_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000002")
TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000010")


@pytest.fixture
def registry(tmp_path) -> TemplateRegistry:
    store = LocalObjectStore(base_path=tmp_path / "storage")
    return TemplateRegistry(storage=store)


def test_template_version_creation_and_lifecycle(registry: TemplateRegistry) -> None:
    """Verifies template creation, version upload, and approved lifecycle."""
    tmpl = registry.create_template(
        tenant_id=TENANT_ID,
        doc_type="sale_deed",
        property_category="plot",
        language="mr",
        name="Marathi Plot Sale Deed",
        actor_id=SUBMITTER_ID,
    )

    docx_sample = b"PK\x03\x04sample-docx-bytes"
    manifest = {"manifest_schema": 1, "fields": ["property.mouza"]}

    # Upload version 1
    v1 = registry.upload_version(
        template_id=tmpl.id,
        manifest=manifest,
        docx_bytes=docx_sample,
        created_by=SUBMITTER_ID,
    )
    assert v1.version == 1
    assert v1.status == "draft"
    assert registry.storage.exists(v1.file_ref) is True

    # Submit for review
    v1 = registry.submit_for_review(v1.id)
    assert v1.status == "under_review"

    # Separation of duties: Submitter CANNOT approve
    with pytest.raises(PermissionError):
        registry.approve_version(v1.id, reviewer_id=SUBMITTER_ID)

    # Legitimate reviewer approves
    v1_approved = registry.approve_version(v1.id, reviewer_id=REVIEWER_ID)
    assert v1_approved.status == "approved"
    assert v1_approved.approved_by == REVIEWER_ID
    assert v1_approved.approved_at is not None


def test_immutable_approved_template_version(registry: TemplateRegistry) -> None:
    """AGENTS.md Hard Rule 3: Never modify an approved template version."""
    tmpl = registry.create_template(
        tenant_id=TENANT_ID,
        doc_type="sale_deed",
        language="mr",
        name="Marathi Deed",
    )
    v1 = registry.upload_version(tmpl.id, {"fields": []}, b"DOCX", created_by=SUBMITTER_ID)
    registry.submit_for_review(v1.id)
    registry.approve_version(v1.id, reviewer_id=REVIEWER_ID)

    # Attempting to modify approved version must fail!
    with pytest.raises(TemplateImmutabilityError):
        registry.update_version_content(v1.id, new_manifest={"fields": ["illegal"]})

