"""Property domain data records."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class PropertyRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    category: str
    attrs: dict[str, Any]
    area_value: Decimal | None = None
    area_unit: str | None = None
    boundaries: dict[str, Any] | None = None
    rr_division: str | None = None
    rr_rate: Decimal | None = None
    version: int = 1
    deleted: bool = False


@dataclass
class PropertyVersionRecord:
    property_id: uuid.UUID
    version: int
    data: dict[str, Any]
    changed_by: uuid.UUID | None = None
