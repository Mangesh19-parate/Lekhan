"""Automated Scratch DB Restore Drill with Cryptographic Audit Chain Verification.

Adheres strictly to PRD FR-18, Features F-070, and ARCHITECTURE.md Section 11:
1. Provisions scratch state with authentic SHA-256 chained audit logs and counters.
2. Generates an atomic checksummed backup archive.
3. Simulates catastrophic disaster / scratch DB wipe.
4. Executes full restore from the backup archive.
5. Verifies cryptographic audit chain integrity across all restored tenants.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import uuid
from pathlib import Path

from app.audit.jobs import verify_all_audit_chains
from app.audit.service import audit_service
from app.numbering.service import document_numbering_service
from app.shared.logging import get_logger, setup_logging
from scripts.backup import create_backup
from scripts.restore import restore_backup

setup_logging()
logger = get_logger("restore_drill")


def run_restore_drill() -> bool:
    """Executes the full automated restore drill and checks the audit chain."""
    logger.info("Starting automated backup & scratch DB restore drill...")

    stage_dir = Path(tempfile.mkdtemp(prefix="drill_run_"))
    backup_dest = stage_dir / "backups"
    storage_dest = stage_dir / "storage"
    backup_dest.mkdir(parents=True, exist_ok=True)
    storage_dest.mkdir(parents=True, exist_ok=True)

    tenant_1 = uuid.uuid4()
    tenant_2 = uuid.uuid4()

    try:
        # 0. Ensure database tables and test tenants exist for foreign key integrity
        try:
            from app.adapters.db import SessionLocal, engine
            from app.shared.models import Base, Tenant

            Base.metadata.create_all(engine)
            with SessionLocal() as session:
                for tid, tname in [(tenant_1, "Drill Tenant 1"), (tenant_2, "Drill Tenant 2")]:
                    if not session.get(Tenant, tid):
                        session.add(Tenant(id=tid, name=tname, slug=f"drill-{tid.hex[:8]}"))
                session.commit()
        except Exception as exc:
            logger.debug("Database setup skipped or running in-memory: %s", exc)

        # 1. Populate state with chained audit logs and sequence counters
        audit_service.log_event(
            tenant_id=tenant_1, action="tenant_created", entity="tenant", entity_id=str(tenant_1)
        )
        audit_service.log_event(
            tenant_id=tenant_1,
            action="document_created",
            entity="document",
            entity_id="DOC/2026/001",
        )
        audit_service.log_event(
            tenant_id=tenant_1,
            action="finalise_document",
            entity="document",
            entity_id="DOC/2026/001",
        )

        audit_service.log_event(
            tenant_id=tenant_2, action="tenant_created", entity="tenant", entity_id=str(tenant_2)
        )
        audit_service.log_event(
            tenant_id=tenant_2, action="template_approved", entity="template", entity_id="tmpl_001"
        )

        document_numbering_service.set_counter(tenant_1, "DOC", 2026, 42)
        document_numbering_service.set_counter(tenant_2, "DOC", 2026, 7)

        # Confirm initial chain is healthy
        initial_check = verify_all_audit_chains()
        if initial_check.status != "healthy":
            logger.error(
                "Initial audit chain unhealthy before backup: %s", initial_check.broken_tenants
            )
            return False

        logger.info(
            "Pre-backup audit chain verified across %d tenants.", initial_check.tenants_checked
        )

        # 2. Create atomic backup
        archive_path = create_backup(destination_dir=backup_dest, include_storage=True)
        logger.info("Backup archive successfully created: %s", archive_path.name)

        # 3. Simulate disaster: wipe audit logs and reset counters
        audit_service.clear()
        document_numbering_service.clear()

        # 4. Perform restore into scratch environment
        report = restore_backup(archive_path=archive_path, target_storage_dir=storage_dest)
        logger.info("Restore completed with status: %s", report.get("status"))

        # 5. Verify restored audit chain integrity
        restored_check = verify_all_audit_chains()
        if restored_check.status != "healthy":
            logger.critical(
                "DRILL FAILED: Restored audit chain contains broken hash links: %s",
                restored_check.broken_tenants,
            )
            return False

        # 6. Verify restored sequential counters
        c1 = document_numbering_service.get_counter(tenant_1, "DOC", 2026)
        c2 = document_numbering_service.get_counter(tenant_2, "DOC", 2026)
        if c1 != 42 or c2 != 7:
            logger.critical(
                "DRILL FAILED: Restored counters do not match pre-backup values (got %s, %s)",
                c1,
                c2,
            )
            return False

        logger.info(
            "DRILL PASSED: All %d tenants restored, counters validated, and cryptographic audit chain 100%% verified.",
            restored_check.tenants_checked,
        )
        return True

    finally:
        shutil.rmtree(stage_dir, ignore_errors=True)


if __name__ == "__main__":
    success = run_restore_drill()
    sys.exit(0 if success else 1)
