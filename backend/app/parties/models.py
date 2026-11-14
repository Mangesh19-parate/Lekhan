"""Party domain data records."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class PartyRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    kind: str
    gender: str | None
    marital_status: str | None
    age_or_dob: dict[str, Any] | None
    names: dict[str, Any]
    occupations: dict[str, Any]
    addresses: dict[str, Any]
    pan_masked: str | None = None
    version: int = 1
    deleted: bool = False


@dataclass
class PartyVersionRecord:
    party_id: uuid.UUID
    version: int
    data: dict[str, Any]
    changed_by: uuid.UUID | None = None
