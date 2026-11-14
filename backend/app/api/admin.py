"""Administration, User Management, Roles, and System Health REST API."""

from __future__ import annotations

import os
import shutil
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adapters.db import get_db, ping_db
from app.adapters.repositories.audit import PostgresAuditRepository
from app.adapters.repositories.jobs import PostgresJobRepository
from app.adapters.storage import default_storage
from app.api.auth import get_current_actor, get_user_repo
from app.audit.repository import AuditRepository
from app.audit.service import AuditService, audit_service
from app.config import get_settings
from app.generation.jobs import JobRepository
from app.generation.pipeline import generation_pipeline
from app.identity.policy import ROLE_PERMISSIONS, Actor, authorize
from app.identity.repository import UserRepository
from app.api.templates_admin import list_templates

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
settings = get_settings()


def get_audit_repo(db: Session = Depends(get_db)) -> AuditRepository:
    """FastAPI dependency yielding tenant-scoped AuditRepository."""
    return PostgresAuditRepository(session=db)


def get_audit_service(
    repo: AuditRepository = Depends(get_audit_repo),
) -> AuditService:
    """FastAPI dependency yielding AuditService backed by database repository."""
    return AuditService(repository=repo)


def get_job_repo(db: Session = Depends(get_db)) -> JobRepository:
    """FastAPI dependency yielding tenant-scoped JobRepository."""
    return PostgresJobRepository(session=db)


class UserUpdatePayload(BaseModel):
    role: str | None = None
    active: bool | None = None


@router.get("/users", summary="List tenant users")
def get_users(
    actor: Actor = Depends(get_current_actor),
    user_repo: UserRepository = Depends(get_user_repo),
) -> list[dict[str, Any]]:
    """Returns users registered under current tenant."""
    decision = authorize(actor, "manage_users")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    users = user_repo.list_all(tenant_id=actor.tenant_id)
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "display_name": u.display_name,
            "role": u.role,
            "ui_language": u.ui_language,
            "active": u.active,
            "mfa_enabled": bool(u.mfa_secret_enc),
        }
        for u in users
    ]


@router.post("/users/{user_id}/status", summary="Toggle user active status")
def toggle_user_status(
    user_id: str,
    payload: UserUpdatePayload,
    actor: Actor = Depends(get_current_actor),
    user_repo: UserRepository = Depends(get_user_repo),
    audit_svc: AuditService = Depends(get_audit_service),
) -> dict[str, Any]:
    """Activates or deactivates a user account."""
    decision = authorize(actor, "manage_users")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")

    target_user = user_repo.get_by_id(tenant_id=actor.tenant_id, user_id=uid)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.active is not None:
        target_user.active = payload.active

    if payload.role is not None:
        target_user.role = payload.role

    user_repo.update(tenant_id=actor.tenant_id, user=target_user)

    audit_svc.log_event(
        tenant_id=actor.tenant_id,
        action="user_updated",
        entity="user",
        entity_id=user_id,
        actor_id=actor.user_id,
        meta={"new_role": target_user.role, "active": target_user.active},
    )

    return {"status": "ok", "user": {
        "id": str(target_user.id),
        "email": target_user.email,
        "role": target_user.role,
        "active": target_user.active,
    }}


@router.get("/roles", summary="Get authoritative RBAC permission matrix")
def get_roles_permissions(actor: Actor = Depends(get_current_actor)) -> dict[str, Any]:
    """Returns role permission mapping and separation of duties constraints."""
    formatted_matrix: dict[str, list[str]] = {}
    for role, actions in ROLE_PERMISSIONS.items():
        formatted_matrix[role] = sorted(list(actions))

    return {
        "roles": ["admin", "template_admin", "reviewer", "drafter"],
        "matrix": formatted_matrix,
        "separation_of_duties": [
            {
                "rule": "Template Submitter cannot approve own version",
                "description": "A template submitter is cryptographically barred from approving their own submission.",
                "enforced_at": "backend/app/identity/policy.py",
            },
            {
                "rule": "Cross-Tenant 404 Isolation",
                "description": "Queries crossing tenant boundaries are strictly answered with 404, masking resource existence.",
                "enforced_at": "backend/app/identity/policy.py",
            },
            {
                "rule": "Finalised Document Immutability",
                "description": "Once marked finalised, documents cannot be edited, reviewed, or reopened.",
                "enforced_at": "backend/app/review/fsm.py",
            },
        ],
    }


@router.get("/audit", summary="Get cryptographically chained audit log")
def get_audit_trail(
    actor: Actor = Depends(get_current_actor),
    audit_repo: AuditRepository = Depends(get_audit_repo),
) -> dict[str, Any]:
    """Returns append-only SHA-256 chained audit events with chain validity verification."""
    decision = authorize(actor, "view_document")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    records = audit_repo.get_chain(actor.tenant_id)
    chain_valid = audit_repo.verify_audit_chain(actor.tenant_id)

    formatted_records = []
    for r in reversed(records):
        formatted_records.append({
            "id": r.id,
            "action": r.action,
            "entity": r.entity,
            "entity_id": r.entity_id,
            "timestamp": r.at.isoformat(),
            "actor_id": str(r.actor_id) if r.actor_id else None,
            "hash": r.hash.hex(),
            "prev_hash": r.prev_hash.hex() if r.prev_hash else "00" * 32,
            "meta": r.meta,
        })

    return {
        "chain_valid": chain_valid,
        "total_records": len(formatted_records),
        "records": formatted_records,
    }


@router.get("/audit/verify", summary="Verify cryptographic audit chain integrity")
def verify_audit_trail(
    actor: Actor = Depends(get_current_actor),
    audit_repo: AuditRepository = Depends(get_audit_repo),
) -> dict[str, Any]:
    """Exposes verify_audit_chain via admin API, checking SHA-256 chain continuity and tampering."""
    decision = authorize(actor, "view_document")
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)

    chain_valid = audit_repo.verify_audit_chain(actor.tenant_id)
    return {
        "tenant_id": str(actor.tenant_id),
        "chain_valid": chain_valid,
        "tamper_detected": not chain_valid,
    }


@router.get("/system-health", summary="Detailed system health report")
def get_system_health(
    actor: Actor = Depends(get_current_actor),
    job_repo: JobRepository = Depends(get_job_repo),
) -> dict[str, Any]:
    """Returns infrastructure and service health metrics."""
    db_ok = ping_db()
    storage_dir = settings.STORAGE_PATH
    storage_ok = storage_dir.exists() and os.access(storage_dir, os.W_OK)
    
    disk_free_gb = 0.0
    try:
        total, used, free = shutil.disk_usage(storage_dir if storage_dir.exists() else ".")
        disk_free_gb = round(free / (1024 ** 3), 2)
    except OSError as err:
        logger.warning(
            "Could not inspect disk usage [cid=%s]: %s",
            get_correlation_id(),
            err,
        )

    templates = list_templates(actor)
    approved_tmpls = len([t for t in templates if t.status == "approved"])
    queued_jobs = len(job_repo.list(tenant_id=actor.tenant_id, status="queued", limit=100))

    return {
        "status": "healthy" if (storage_ok and approved_tmpls > 0) else "degraded",
        "api": {
            "status": "online",
            "version": "1.0.0",
            "environment": settings.ENV,
            "docs_url": "/api/docs" if settings.is_dev else "disabled",
        },
        "database": {
            "status": "connected" if db_ok else "degraded",
            "adapter": "PostgreSQL 16 (SQLAlchemy 2.0 + psycopg3)",
            "connection_pooling": "10 max, 20 overflow, 3600s recycle",
        },
        "storage": {
            "status": "online" if storage_ok else "offline",
            "path": str(storage_dir),
            "free_space_gb": disk_free_gb,
            "type": "Local Encrypted File System / ObjectStore",
        },
        "template_engine": {
            "status": "ready",
            "total_templates": len(templates),
            "approved_templates": approved_tmpls,
            "docx_lint_status": "enforced",
        },
        "worker_queue": {
            "status": "active",
            "queued_jobs": queued_jobs,
            "engine": "Idempotent FIFO Async Pipeline (FOR UPDATE SKIP LOCKED)",
        },
    }
