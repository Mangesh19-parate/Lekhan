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
    area_value: Decimal | None
    area_unit: str | None
    boundaries: dict[str, Any] | None
    rr_division: str | None
    rr_rate: Decimal | None
    version: int
    deleted: bool = False


@dataclass
class PropertyVersionRecord:
    property_id: uuid.UUID
    version: int
    data: dict[str, Any]
    changed_by: uuid.UUID | None

