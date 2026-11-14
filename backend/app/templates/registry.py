"""Template registry service with immutable version guarantees.

Enforces:
- AGENTS.md Hard Rule 3: Never modify an approved template version. Create a new version.
- Separation of duties: The creator/submitter cannot approve their own template version.
- SHA-256 integrity verification on file storage.
- FSM Lifecycle: draft -> under_review -> approved -> retired.
"""

from __future__ import annotations

import datetime
import hashlib
import uuid
from dataclasses import dataclass
from typing import Any

from app.adapters.storage import ObjectStore, default_storage
from app.audit.service import audit_service
from app.shared.errors import AppError
from app.shared.ids import uuid7
from app.shared.logging import get_correlation_id, get_logger

logger = get_logger(__name__)


class TemplateImmutabilityError(AppError):
    """Raised when attempting to modify an approved or retired template version."""

    def __init__(
        self, message: str = "Approved template versions are immutable. Create a new version."
    ) -> None:
        super().__init__(message=message, code="TEMPLATE_IMMUTABLE", status_code=409)


@dataclass
class TemplateRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    doc_type: str
    property_category: str | None
    language: str
    name: str
    created_at: datetime.datetime


@dataclass
class TemplateVersionRecord:
    id: uuid.UUID
    template_id: uuid.UUID
    version: int
    manifest_schema: int
    manifest: dict[str, Any]
    file_ref: str
    file_sha256: bytes
    status: str  # draft, under_review, approved, retired
    created_by: uuid.UUID | None
    approved_by: uuid.UUID | None = None
    approved_at: datetime.datetime | None = None
    created_at: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
    lint_report: dict[str, Any] | None = None


class TemplateRegistry:
    """Manages legal templates and immutable version lifecycles."""

    def __init__(self, storage: ObjectStore = default_storage) -> None:
        self.storage = storage
        self._templates: dict[uuid.UUID, TemplateRecord] = {}
        self._versions: dict[uuid.UUID, TemplateVersionRecord] = {}

    def create_template(
        self,
        tenant_id: uuid.UUID | None,
        doc_type: str,
        language: str,
        name: str,
        property_category: str | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> TemplateRecord:
        """Registers a new template header."""
        template_id = uuid7()
        now = datetime.datetime.now(datetime.timezone.utc)
        record = TemplateRecord(
            id=template_id,
            tenant_id=tenant_id,
            doc_type=doc_type,
            property_category=property_category,
            language=language,
            name=name,
            created_at=now,
        )
        self._templates[template_id] = record

        if tenant_id:
            audit_service.log_event(
                tenant_id=tenant_id,
                actor_id=actor_id,
                action="template_created",
                entity="template",
                entity_id=str(template_id),
                meta={"name": name, "doc_type": doc_type},
            )
        return record

    def upload_version(
        self,
        template_id: uuid.UUID,
        manifest: dict[str, Any],
        docx_bytes: bytes,
        manifest_schema: int = 1,
        created_by: uuid.UUID | None = None,
    ) -> TemplateVersionRecord:
        """Uploads a new draft template version. Computes SHA-256 and stores file atomically."""
        if template_id not in self._templates:
            raise KeyError(f"Template {template_id} not found.")

        # Determine next sequential version number
        existing_versions = [
            v.version for v in self._versions.values() if v.template_id == template_id
        ]
        next_version = (max(existing_versions) + 1) if existing_versions else 1

        # Run DOCX lint and repair split runs if valid archive
        lint_report = None
        if docx_bytes.startswith(b"PK") and len(docx_bytes) > 200:
            try:
                from app.templates.lint import default_linter

                repaired_bytes, report = default_linter.lint_and_repair(docx_bytes, manifest)
                docx_bytes = repaired_bytes
                lint_report = report.to_dict()
            except Exception as lint_err:
                cid = get_correlation_id()
                logger.warning(
                    "Linter could not complete automated repair on template %s [cid=%s]: %s",
                    template_id,
                    cid,
                    lint_err,
                )

        file_sha256 = hashlib.sha256(docx_bytes).digest()
        file_key = f"templates/{template_id}/v{next_version}.docx"
        self.storage.put(
            file_key,
            docx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        version_id = uuid7()
        version_record = TemplateVersionRecord(
            id=version_id,
            template_id=template_id,
            version=next_version,
            manifest_schema=manifest_schema,
            manifest=manifest,
            file_ref=file_key,
            file_sha256=file_sha256,
            status="draft",
            created_by=created_by,
            lint_report=lint_report,
        )
        self._versions[version_id] = version_record
        return version_record

    def submit_for_review(self, version_id: uuid.UUID) -> TemplateVersionRecord:
        """Transitions template version from draft to under_review."""
        version = self._versions.get(version_id)
        if not version:
            raise KeyError(f"Template version {version_id} not found.")

        if version.status != "draft":
            raise ValueError(
                f"Cannot submit template in status '{version.status}'. Expected 'draft'."
            )

        if version.manifest_schema == 1:
            from app.templates.compiler import ManifestCompiler

            ManifestCompiler().compile(version.manifest)

        version.status = "under_review"
        return version

    def approve_version(
        self, version_id: uuid.UUID, reviewer_id: uuid.UUID
    ) -> TemplateVersionRecord:
        """Approves a template version, enforcing separation of duties and freezing immutability."""
        version = self._versions.get(version_id)
        if not version:
            raise KeyError(f"Template version {version_id} not found.")

        if version.status != "under_review":
            raise ValueError(
                f"Cannot approve template in status '{version.status}'. Expected 'under_review'."
            )

        # Separation of duties: submitter/creator cannot approve own template version
        if version.created_by is not None and version.created_by == reviewer_id:
            raise PermissionError(
                "Separation of duties violation: Submitter cannot approve their own template version."
            )

        # Hard Rule: DOCX lint errors or leftover client data block approval
        if version.lint_report and not version.lint_report.get("can_approve", True):
            raise ValueError(
                "Template approval blocked: DOCX lint or leftover client data checks failed."
            )

        now = datetime.datetime.now(datetime.timezone.utc)
        version.status = "approved"
        version.approved_by = reviewer_id
        version.approved_at = now

        template = self._templates[version.template_id]
        if template.tenant_id:
            audit_service.log_event(
                tenant_id=template.tenant_id,
                actor_id=reviewer_id,
                action="template_version_approved",
                entity="template_version",
                entity_id=str(version_id),
                meta={"version": version.version},
            )

        return version

    def update_version_content(self, version_id: uuid.UUID, new_manifest: dict[str, Any]) -> None:
        """Modifies draft template manifest. Fails if version is already approved."""
        version = self._versions.get(version_id)
        if not version:
            raise KeyError(f"Template version {version_id} not found.")

        # Hard Rule 3: Never modify an approved template version
        if version.status in ("approved", "retired"):
            raise TemplateImmutabilityError(
                f"Cannot edit template version {version.version} in '{version.status}' status. Create a new version."
            )

        version.manifest = new_manifest

    def get_version(self, version_id: uuid.UUID) -> TemplateVersionRecord | None:
        return self._versions.get(version_id)

    def get_template(self, template_id: uuid.UUID) -> TemplateRecord | None:
        return self._templates.get(template_id)

    def clear(self) -> None:
        self._templates.clear()
        self._versions.clear()


template_registry = TemplateRegistry()
