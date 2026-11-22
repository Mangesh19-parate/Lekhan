"""Cryptographic append-only audit trail service (docs/FEATURES.md F-007).

Implements:
- SHA-256 hash chaining across tenant audit logs
- Tamper detection verification (verify_audit_chain)
- Zero personal data in logs (IDs and event metadata only per AGENTS.md Rule 5)
- Repository-backed persistence (InMemoryAuditRepository or PostgresAuditRepository)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.audit.repository import (
    AuditRecord,
    AuditRepository,
    InMemoryAuditRepository,
    compute_audit_hash,
)
from app.shared.logging import get_logger

logger = get_logger(__name__)

__all__ = [
    "AuditRecord",
    "AuditRepository",
    "AuditService",
    "InMemoryAuditRepository",
    "audit_service",
    "compute_audit_hash",
]


class AuditService:
    """Audit log service with repository-backed tracking & hash-chain verification."""

    def __init__(self, repository: AuditRepository | None = None) -> None:
        self._repository: AuditRepository = (
            repository if repository is not None else InMemoryAuditRepository()
        )

    @property
    def _logs(self) -> dict[uuid.UUID, list[AuditRecord]]:
        """Access internal log dictionary for backward-compatible tests & utilities."""
        if hasattr(self._repository, "_logs"):
            return self._repository._logs  # type: ignore[no-any-return]
        return {}

    def log_event(
        self,
        tenant_id: uuid.UUID,
        action: str,
        entity: str,
        entity_id: str | None = None,
        actor_id: uuid.UUID | None = None,
        meta: dict[str, Any] | None = None,
    ) -> AuditRecord:
        """Appends an immutable audit event linked to the previous entry via SHA-256."""
        now = datetime.now(timezone.utc)
        meta_dict = meta or {}

        last_record = self._repository.get_last_record(tenant_id)
        prev_hash = last_record.hash if last_record else None

        current_hash = compute_audit_hash(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            at=now,
            meta=meta_dict,
            prev_hash=prev_hash,
        )

        record = AuditRecord(
            id=0,  # Will be assigned by repository
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            at=now,
            meta=meta_dict,
            prev_hash=prev_hash,
            hash=current_hash,
        )

        return self._repository.append(tenant_id, record)

    def get_chain(
        self, tenant_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[AuditRecord]:
        """Returns the audit chain for the tenant."""
        return self._repository.get_chain(tenant_id=tenant_id, limit=limit, offset=offset)

    def verify_audit_chain(self, tenant_id: uuid.UUID) -> bool:
        """Verifies the integrity of the audit chain for a tenant.

        Returns False if any record has been modified, deleted, or reordered.
        """
        return self._repository.verify_chain(tenant_id)

    def verify_chain(self, tenant_id: uuid.UUID) -> bool:
        """Alias for verify_audit_chain."""
        return self.verify_audit_chain(tenant_id)

    def clear(self, tenant_id: uuid.UUID | None = None) -> None:
        """Clears logs (test fixture helper)."""
        self._repository.clear(tenant_id)


audit_service = AuditService()
