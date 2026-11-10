"""Cryptographic append-only audit trail service (docs/FEATURES.md F-007).

Implements:
- SHA-256 hash chaining across tenant audit logs
- Tamper detection verification (verify_audit_chain)
- Zero personal data in logs (IDs and event metadata only per AGENTS.md Rule 5)
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

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


class AuditService:
    """Audit log service with in-memory tracking & hash-chain verification."""

    def __init__(self) -> None:
        # In-memory store per tenant (mirrored to PostgreSQL audit_log table in DB adapter)
        self._logs: dict[uuid.UUID, list[AuditRecord]] = {}
        self._next_id = 1

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

        tenant_chain = self._logs.setdefault(tenant_id, [])
        prev_hash = tenant_chain[-1].hash if tenant_chain else None

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
            id=self._next_id,
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
        self._next_id += 1
        tenant_chain.append(record)
        return record

    def verify_audit_chain(self, tenant_id: uuid.UUID) -> bool:
        """Verifies the integrity of the audit chain for a tenant.

        Returns False if any record has been modified, deleted, or reordered.
        """
        chain = self._logs.get(tenant_id, [])
        if not chain:
            return True

        expected_prev: bytes | None = None
        for record in chain:
            # 1. Check previous hash continuity
            if record.prev_hash != expected_prev:
                logger.error("Audit chain broken at record %d: prev_hash mismatch", record.id)
                return False

            # 2. Recompute hash
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
                logger.error("Audit chain broken at record %d: digest mismatch (tampered content)", record.id)
                return False

            expected_prev = record.hash

        return True

    def clear(self) -> None:
        """Clears memory logs (test fixture helper)."""
        self._logs.clear()
        self._next_id = 1


audit_service = AuditService()

