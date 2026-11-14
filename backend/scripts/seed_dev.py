"""Synthetic Dev Data Seeding Script (AGENTS.md Hard Rule 1 & Section 4 `make seed`).

Strictly synthetic data only. Seeds:
1. Dev Tenants (Primary Nagpur Firm, Secondary External Firm)
2. Synthetic User Accounts with Argon2id password hashes:
   - admin@lekhan.local (Role: admin)
   - drafter@lekhan.local (Role: drafter)
   - reviewer@lekhan.local (Role: reviewer)
   - template_admin@lekhan.local (Role: template_admin)
   - other_tenant@lekhan.local (Role: drafter, secondary tenant for cross-tenant testing)
"""

from __future__ import annotations

import uuid
from typing import Any

from app.adapters.db import SessionLocal
from app.shared.logging import get_logger
from app.shared.models import Tenant, User
from app.shared.security import hash_password

logger = get_logger(__name__)

# Primary Dev Tenant
PRIMARY_TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000000")
# Secondary Tenant for cross-tenant isolation verification
SECONDARY_TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000099")

DEV_TENANTS: list[dict[str, Any]] = [
    {
        "id": PRIMARY_TENANT_ID,
        "name": "Dev Legal Associates (Nagpur)",
        "settings": {"jurisdiction": "Maharashtra", "default_language": "mr"},
        "feature_flags": {"enable_kruti_converter": True, "enable_ai_advisory": True},
    },
    {
        "id": SECONDARY_TENANT_ID,
        "name": "External Law Chambers (Secondary)",
        "settings": {"jurisdiction": "Maharashtra", "default_language": "en"},
        "feature_flags": {"enable_kruti_converter": False},
    },
]

DEV_USERS: list[dict[str, Any]] = [
    {
        "id": uuid.UUID("0193132e-504f-7a1b-8000-000000000001"),
        "tenant_id": PRIMARY_TENANT_ID,
        "email": "admin@lekhan.local",
        "display_name": "Senior Partner (Admin)",
        "password": "ValidPassword123!",
        "role": "admin",
        "ui_language": "mr",
    },
    {
        "id": uuid.UUID("0193132e-504f-7a1b-8000-000000000002"),
        "tenant_id": PRIMARY_TENANT_ID,
        "email": "drafter@lekhan.local",
        "display_name": "Advocate Drafter (Nagpur)",
        "password": "ValidPassword123!",
        "role": "drafter",
        "ui_language": "mr",
    },
    {
        "id": uuid.UUID("0193132e-504f-7a1b-8000-000000000003"),
        "tenant_id": PRIMARY_TENANT_ID,
        "email": "reviewer@lekhan.local",
        "display_name": "Reviewer Advocate",
        "password": "ValidPassword123!",
        "role": "reviewer",
        "ui_language": "mr",
    },
    {
        "id": uuid.UUID("0193132e-504f-7a1b-8000-000000000004"),
        "tenant_id": PRIMARY_TENANT_ID,
        "email": "template_admin@lekhan.local",
        "display_name": "Template Administrator",
        "password": "ValidPassword123!",
        "role": "template_admin",
        "ui_language": "en",
    },
    {
        "id": uuid.UUID("0193132e-504f-7a1b-8000-000000000099"),
        "tenant_id": SECONDARY_TENANT_ID,
        "email": "other_tenant@lekhan.local",
        "display_name": "External Tenant User",
        "password": "ValidPassword123!",
        "role": "drafter",
        "ui_language": "en",
    },
]


def seed_dev_data() -> dict[str, int]:
    """Inserts or updates dev tenants and synthetic dev users in the PostgreSQL database."""
    tenants_seeded = 0
    users_seeded = 0

    with SessionLocal() as session:
        # 1. Upsert Tenants
        for t in DEV_TENANTS:
            tenant = session.query(Tenant).filter(Tenant.id == t["id"]).first()
            if not tenant:
                tenant = Tenant(
                    id=t["id"],
                    name=t["name"],
                    settings=t["settings"],
                    feature_flags=t["feature_flags"],
                )
                session.add(tenant)
                tenants_seeded += 1
            else:
                tenant.name = t["name"]
                tenant.settings = t["settings"]
                tenant.feature_flags = t["feature_flags"]

        session.flush()

        # 2. Upsert Users with Argon2id hashes
        for u in DEV_USERS:
            user = session.query(User).filter(User.id == u["id"]).first()
            pwd_hash = hash_password(u["password"])
            if not user:
                user = User(
                    id=u["id"],
                    tenant_id=u["tenant_id"],
                    email=u["email"],
                    display_name=u["display_name"],
                    password_hash=pwd_hash,
                    role=u["role"],
                    ui_language=u["ui_language"],
                    active=True,
                )
                session.add(user)
                users_seeded += 1
            else:
                user.email = u["email"]
                user.display_name = u["display_name"]
                user.password_hash = pwd_hash
                user.role = u["role"]
                user.ui_language = u["ui_language"]
                user.active = True

        session.commit()

    logger.info("Dev seed complete: %d tenants, %d users.", tenants_seeded, users_seeded)
    return {"tenants": tenants_seeded, "users": users_seeded}


if __name__ == "__main__":
    results = seed_dev_data()
    print(f"Seed dev data completed: {results}")
