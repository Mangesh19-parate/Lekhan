"""PostgreSQL implementation of the AuditRepository protocol.

Uses SQLAlchemy 2.0 Session to interact with `audit_log` table.
Enforces strict tenant scoping and cryptographic SHA-256 verification.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.adapters.db import SessionLocal
from app.audit.repository import AuditRecord, compute_audit_hash
from app.shared.logging import get_logger
from app.shared.models import AuditLog as AuditLogModel

logger = get_logger(__name__)


def _to_record(model: AuditLogModel) -> AuditRecord:
    """Converts a SQLAlchemy AuditLogModel to pure domain AuditRecord."""
    return AuditRecord(
        id=model.id,
        tenant_id=model.tenant_id,
        actor_id=model.actor_id,
        action=model.action,
        entity=model.entity,
        entity_id=model.entity_id,
        at=model.at,
        meta=dict(model.meta or {}),
        prev_hash=bytes(model.prev_hash) if model.prev_hash is not None else None,
        hash=bytes(model.hash),
    )


class PostgresAuditRepository:
    """Production PostgreSQL audit repository implementing AuditRepository."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def _get_session(self) -> Session:
        return self._session if self._session is not None else SessionLocal()

    def append(self, tenant_id: uuid.UUID, record: AuditRecord) -> AuditRecord:
        """Appends an immutable audit entry to the tenant's cryptographic log."""
        if record.tenant_id != tenant_id:
            raise ValueError(
                f"Cross-tenant audit append rejected: record tenant {record.tenant_id} != {tenant_id}"
            )

        session = self._get_session()
        should_close = self._session is None
        try:
            db_record = AuditLogModel(
                tenant_id=tenant_id,
                actor_id=record.actor_id,
                action=record.action,
                entity=record.entity,
                entity_id=record.entity_id,
                at=record.at,
                meta=record.meta,
                prev_hash=record.prev_hash,
                hash=record.hash,
            )
            session.add(db_record)
            session.commit()
            session.refresh(db_record)
            return _to_record(db_record)
        except Exception:
            session.rollback()
            raise
        finally:
            if should_close:
                session.close()

    def get_last_record(self, tenant_id: uuid.UUID) -> AuditRecord | None:
        """Retrieves the latest audit entry in the tenant's chain to resolve prev_hash."""
        session = self._get_session()
        should_close = self._session is None
        try:
            stmt = (
                select(AuditLogModel)
                .where(AuditLogModel.tenant_id == tenant_id)
                .order_by(AuditLogModel.id.desc())
                .limit(1)
            )
            model = session.execute(stmt).scalars().first()
            return _to_record(model) if model else None
        finally:
            if should_close:
                session.close()

    def get_chain(
        self, tenant_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[AuditRecord]:
        """Retrieves tenant audit records in ascending order of sequence."""
        session = self._get_session()
        should_close = self._session is None
        try:
            stmt = (
                select(AuditLogModel)
                .where(AuditLogModel.tenant_id == tenant_id)
                .order_by(AuditLogModel.id.asc())
                .offset(offset)
                .limit(limit)
            )
            rows = session.execute(stmt).scalars().all()
            return [_to_record(r) for r in rows]
        finally:
            if should_close:
                session.close()

    def verify_audit_chain(self, tenant_id: uuid.UUID) -> bool:
        """Verifies the integrity of the cryptographic SHA-256 chain for tenant."""
        session = self._get_session()
        should_close = self._session is None
        try:
            stmt = (
                select(AuditLogModel)
                .where(AuditLogModel.tenant_id == tenant_id)
                .order_by(AuditLogModel.id.asc())
            )
            rows = session.execute(stmt).scalars().all()
            if not rows:
                return True

            records = [_to_record(r) for r in rows]
            expected_prev: bytes | None = None

            for record in records:
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
                        "Audit chain broken at record %d: digest mismatch (tampered content)",
                        record.id,
                    )
                    return False

                expected_prev = record.hash

            return True
        finally:
            if should_close:
                session.close()

    def verify_chain(self, tenant_id: uuid.UUID) -> bool:
        return self.verify_audit_chain(tenant_id)

    def clear(self, tenant_id: uuid.UUID | None = None) -> None:
        """Test fixture helper to clear tenant records."""
        session = self._get_session()
        should_close = self._session is None
        try:
            session.connection().info["allow_audit_cleanup"] = True
            stmt = delete(AuditLogModel)
            if tenant_id is not None:
                stmt = stmt.where(AuditLogModel.tenant_id == tenant_id)
            session.execute(stmt)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            if should_close:
                session.close()
