"""Central backend authorisation policy engine.

Enforces:
- AGENTS.md Hard Rule 6: Authorisation lives in the backend (authorize(actor, action, resource)).
- Every query/action is strictly tenant-scoped (cross-tenant yields 404 NOT_FOUND).
- Separation of duties: A user who submitted a template version CANNOT approve it.
- Deny by default.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

Role = Literal["admin", "template_admin", "reviewer", "drafter"]

Action = Literal[
    # User and Tenant Management
    "manage_users",
    "manage_settings",
    "view_audit_log",
    # Template Platform
    "create_template",
    "upload_template_version",
    "submit_template_for_review",
    "approve_template_version",
    "retire_template",
    # Document Operations
    "create_document",
    "view_document",
    "edit_document",
    "review_document",
    "finalize_document",
    "delete_document",
    "download_document",
]


@dataclass(frozen=True)
class Actor:
    """Authenticated user context."""

    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role: str
    active: bool = True


@dataclass(frozen=True)
class Resource:
    """Target resource context for authorization checks."""

    tenant_id: uuid.UUID
    resource_type: str
    owner_id: uuid.UUID | None = None
    submitter_id: uuid.UUID | None = None
    is_finalized: bool = False


@dataclass(frozen=True)
class Decision:
    """Result of an authorization check."""

    allowed: bool
    reason: str
    status_code: int = 200

    @classmethod
    def allow(cls, reason: str = "Authorized") -> Decision:
        return cls(allowed=True, reason=reason, status_code=200)

    @classmethod
    def deny(cls, reason: str, status_code: int = 403) -> Decision:
        return cls(allowed=False, reason=reason, status_code=status_code)

    @classmethod
    def not_found(cls, reason: str = "Resource not found") -> Decision:
        # Cross-tenant access MUST return 404 per AGENTS.md Hard Rule 6 & docs/AUTH.md Section 8
        return cls(allowed=False, reason=reason, status_code=404)


# Base permissions map per role (docs/AUTH.md Section 7)
ROLE_PERMISSIONS: dict[str, set[Action]] = {
    "admin": {
        "manage_users",
        "manage_settings",
        "view_audit_log",
        "create_document",
        "view_document",
        "edit_document",
        "delete_document",
        "download_document",
        "review_document",
        "finalize_document",
    },
    "template_admin": {
        "create_template",
        "upload_template_version",
        "submit_template_for_review",
        "retire_template",
        "view_document",
        "download_document",
    },
    "reviewer": {
        "approve_template_version",
        "review_document",
        "finalize_document",
        "view_document",
        "download_document",
    },
    "drafter": {
        "create_document",
        "view_document",
        "edit_document",
        "download_document",
    },
}


def authorize(
    actor: Actor,
    action: Action,
    resource: Resource | None = None,
) -> Decision:
    """Evaluates actor permissions against action and resource context."""
    # 1. Inactive users are unconditionally denied
    if not actor.active:
        return Decision.deny("User account is inactive", status_code=403)

    # 2. Cross-tenant check: if resource is provided, tenant_id must match
    if resource is not None:
        if resource.tenant_id != actor.tenant_id:
            # Must return 404 to avoid leaking resource existence across tenants
            return Decision.not_found("Resource not found")

    # 3. Check base role permission
    allowed_actions = ROLE_PERMISSIONS.get(actor.role, set())
    if action not in allowed_actions:
        return Decision.deny(f"Role '{actor.role}' lacks permission for action '{action}'")

    # 4. Contextual Resource Checks
    if resource is not None:
        # Rule: Submitter cannot approve their own template version (Separation of duties)
        if action == "approve_template_version":
            if resource.submitter_id == actor.user_id:
                return Decision.deny("Submitter cannot approve their own template version")

        # Rule: Finalised documents cannot be deleted even by admin
        if action == "delete_document" and resource.is_finalized:
            return Decision.deny("Finalised documents cannot be deleted")

        # Rule: Drafters can only view/edit documents they own
        if actor.role == "drafter" and resource.resource_type == "document":
            if action in ("view_document", "edit_document", "download_document"):
                if resource.owner_id is not None and resource.owner_id != actor.user_id:
                    return Decision.not_found("Resource not found")

    return Decision.allow()

