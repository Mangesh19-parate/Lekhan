"""Nightly audit-chain verification job and alerting.

Periodically verifies cryptographic SHA-256 hash chains across all tenant audit logs.
Triggers critical alerts if any broken link or tampering is detected.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.db import SessionLocal
from app.audit.repository import AuditRepository, InMemoryAuditRepository
from app.audit.service import audit_service
from app.shared.logging import get_correlation_id, get_logger
from app.shared.models import AuditLog as AuditLogModel

logger = get_logger(__name__)


@dataclass
class AuditChainVerificationReport:
    status: str  # "healthy" | "broken"
    tenants_checked: int
    broken_tenants: list[str]
    verified_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "tenants_checked": self.tenants_checked,
            "broken_tenants": self.broken_tenants,
            "verified_at": self.verified_at,
        }


def verify_all_audit_chains(
    session: Session | None = None,
    audit_repo: AuditRepository | None = None,
) -> AuditChainVerificationReport:
    """Iterates through all tenants, validates hash chain continuity, and alerts on broken chain."""
    cid = get_correlation_id()
    now_iso = datetime.now(timezone.utc).isoformat()
    tenant_ids: list[uuid.UUID] = []

    repo = audit_repo or audit_service._repository

    if isinstance(repo, InMemoryAuditRepository):
        tenant_ids = list(repo._logs.keys())
    else:
        # PostgreSQL repository mode
        sess = session if session is not None else SessionLocal()
        should_close = session is None
        try:
            stmt = select(AuditLogModel.tenant_id).distinct()
            tenant_ids = list(sess.scalars(stmt).all())
        finally:
            if should_close:
                sess.close()

    broken_tenants: list[str] = []

    for tid in tenant_ids:
        try:
            is_valid = repo.verify_audit_chain(tid)
            if not is_valid:
                broken_tenants.append(str(tid))
                logger.critical(
                    "AUDIT_CHAIN_INTEGRITY_ALERT: Cryptographic audit chain broken for tenant %s! "
                    "Possible tamper detected in audit_log [cid=%s]",
                    tid,
                    cid,
                )
        except Exception as exc:
            broken_tenants.append(str(tid))
            logger.critical(
                "AUDIT_CHAIN_INTEGRITY_ALERT: Audit verification exception for tenant %s: %s [cid=%s]",
                tid,
                exc,
                cid,
            )

    report = AuditChainVerificationReport(
        status="broken" if broken_tenants else "healthy",
        tenants_checked=len(tenant_ids),
        broken_tenants=broken_tenants,
        verified_at=now_iso,
    )

    if report.status == "healthy":
        logger.info(
            "Audit chain nightly verification completed successfully: %d tenants verified [cid=%s]",
            len(tenant_ids),
            cid,
        )
    else:
        logger.critical(
            "AUDIT_CHAIN_INTEGRITY_ALERT: Nightly audit verification failed for %d tenant(s): %s [cid=%s]",
            len(broken_tenants),
            broken_tenants,
            cid,
        )

    return report
