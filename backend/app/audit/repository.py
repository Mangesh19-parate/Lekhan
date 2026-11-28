"""Audit repository interface and in-memory implementation.

Enforces:
- Tenant-scoped append and retrieval
- Pure Python domain types (no SQLAlchemy/FastAPI imports)
- Deterministic SHA-256 hash chaining verification
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from app.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AuditRecord:
    id: int
    tenant_id: uuid.UUID
    actor_id: uuid.UUID | None
    action: str
    entity: str
    entity_id: str | None
    at: datetime
    meta: dict[str, Any]
    prev_hash: bytes | None
    hash: bytes


def compute_audit_hash(
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    action: str,
    entity: str,
    entity_id: str | None,
    at: datetime,
    meta: dict[str, Any],
    prev_hash: bytes | None,
) -> bytes:
    """Computes deterministic SHA-256 digest for an audit entry."""
    hasher = hashlib.sha256()

    # Prepend previous hash (or 32 zero bytes for genesis entry)
    hasher.update(prev_hash if prev_hash else bytes(32))
    hasher.update(str(tenant_id).encode("utf-8"))
    hasher.update(str(actor_id or "").encode("utf-8"))
    hasher.update(action.encode("utf-8"))
    hasher.update(entity.encode("utf-8"))
    hasher.update(str(entity_id or "").encode("utf-8"))
    hasher.update(at.isoformat().encode("utf-8"))
    # Canonical sorted JSON representation
    hasher.update(json.dumps(meta, sort_keys=True, ensure_ascii=False).encode("utf-8"))

    return hasher.digest()


@runtime_checkable
class AuditRepository(Protocol):
    """Protocol for cryptographic append-only audit trail repositories."""

    def append(self, tenant_id: uuid.UUID, record: AuditRecord) -> AuditRecord:
        """Appends an immutable audit record for the tenant."""
        ...

    def get_last_record(self, tenant_id: uuid.UUID) -> AuditRecord | None:
        """Retrieves the latest audit entry in the tenant's chain to resolve prev_hash."""
        ...

    def get_chain(
        self, tenant_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[AuditRecord]:
        """Retrieves tenant audit records in ascending order of sequence."""
        ...

    def verify_audit_chain(self, tenant_id: uuid.UUID) -> bool:
        """Verifies integrity of the cryptographic SHA-256 chain for tenant."""
        ...

    def verify_chain(self, tenant_id: uuid.UUID) -> bool:
        """Alias for verify_audit_chain."""
        ...

    def clear(self, tenant_id: uuid.UUID | None = None) -> None:
        """Test fixture helper to clear records."""
        ...


class InMemoryAuditRepository:
    """In-memory implementation for unit testing and offline development."""

    def __init__(self) -> None:
        self._logs: dict[uuid.UUID, list[AuditRecord]] = {}
        self._next_id = 1

    def append(self, tenant_id: uuid.UUID, record: AuditRecord) -> AuditRecord:
        if record.tenant_id != tenant_id:
            raise ValueError(f"Cross-tenant append rejected: {record.tenant_id} != {tenant_id}")
        tenant_chain = self._logs.setdefault(tenant_id, [])
        persisted = AuditRecord(
            id=self._next_id,
            tenant_id=tenant_id,
            actor_id=record.actor_id,
            action=record.action,
            entity=record.entity,
            entity_id=record.entity_id,
            at=record.at,
            meta=dict(record.meta),
            prev_hash=record.prev_hash,
            hash=record.hash,
        )
        self._next_id += 1
        tenant_chain.append(persisted)
        return persisted

    def get_last_record(self, tenant_id: uuid.UUID) -> AuditRecord | None:
        chain = self._logs.get(tenant_id, [])
        return chain[-1] if chain else None

    def get_chain(
        self, tenant_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[AuditRecord]:
        chain = self._logs.get(tenant_id, [])
        return chain[offset : offset + limit]

    def verify_audit_chain(self, tenant_id: uuid.UUID) -> bool:
        chain = self._logs.get(tenant_id, [])
        if not chain:
            return True

        expected_prev: bytes | None = None
        for record in chain:
            if record.prev_hash != expected_prev:
                logger.error("Audit chain broken at record %d: prev_hash mismatch", record.id)
                return False

            recomputed = compute_audit_hash(
                tenant_id=record.tenant_id,
                actor_id=record.actor_id,
                action=record.action,
                entity=record.entity,
                entity_id=record.entity_id,
                at=record.at,
                meta=record.meta,
                prev_hash=record.prev_hash,
            )
            if recomputed != record.hash:
                logger.error(
                    "Audit chain broken at record %d: digest mismatch (tampered content)", record.id
                )
                return False

            expected_prev = record.hash

        return True

    def verify_chain(self, tenant_id: uuid.UUID) -> bool:
        return self.verify_audit_chain(tenant_id)

    def clear(self, tenant_id: uuid.UUID | None = None) -> None:
        if tenant_id is not None:
            self._logs.pop(tenant_id, None)
        else:
            self._logs.clear()
            self._next_id = 1
