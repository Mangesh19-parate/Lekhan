"""Pure domain models for identity and user accounts (no ORM/DB dependencies)."""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field


@dataclass
class UserRecord:
    """Domain representation of a tenant user account."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    display_name: str
    password_hash: str
    role: str = "drafter"
    ui_language: str = "mr"
    mfa_secret_enc: bytes | None = None
    active: bool = True
    failed_logins: int = 0
    locked_until: datetime.datetime | None = None
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
