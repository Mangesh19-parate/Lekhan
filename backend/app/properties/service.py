"""Properties domain service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.audit.service import audit_service
from app.shared.concurrency import OptimisticLockError
from app.shared.ids import uuid7


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


class PropertyService:
    """In-memory domain service for property entities."""

    def __init__(self) -> None:
        self._properties: dict[uuid.UUID, PropertyRecord] = {}
        self._versions: list[PropertyVersionRecord] = []

    def create_property(
        self,
        tenant_id: uuid.UUID,
        category: str,
        attrs: dict[str, Any],
        area_value: Decimal | None = None,
        area_unit: str | None = None,
        boundaries: dict[str, Any] | None = None,
        rr_division: str | None = None,
        rr_rate: Decimal | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> PropertyRecord:
        """Creates a property record with version 1."""
        prop_id = uuid7()
        prop = PropertyRecord(
            id=prop_id,
            tenant_id=tenant_id,
            category=category,
            attrs=attrs,
            area_value=area_value,
            area_unit=area_unit,
            boundaries=boundaries,
            rr_division=rr_division,
            rr_rate=rr_rate,
            version=1,
        )
        self._properties[prop_id] = prop

        audit_service.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="property_created",
            entity="property",
            entity_id=str(prop_id),
            meta={"category": category},
        )
        return prop

    def get_property(self, property_id: uuid.UUID, tenant_id: uuid.UUID) -> PropertyRecord | None:
        """Retrieves a property strictly scoped to tenant."""
        prop = self._properties.get(property_id)
        if not prop or prop.tenant_id != tenant_id or prop.deleted:
            return None
        return prop

    def update_property(
        self,
        property_id: uuid.UUID,
        tenant_id: uuid.UUID,
        expected_version: int,
        attrs: dict[str, Any] | None = None,
        boundaries: dict[str, Any] | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> PropertyRecord:
        """Updates property with optimistic locking."""
        prop = self.get_property(property_id, tenant_id)
        if not prop:
            raise KeyError(f"Property {property_id} not found in tenant {tenant_id}")

        if prop.version != expected_version:
            raise OptimisticLockError(
                f"Version conflict on property {property_id}: expected {expected_version}, but found {prop.version}"
            )

        if attrs is not None:
            prop.attrs = attrs
        if boundaries is not None:
            prop.boundaries = boundaries

        prop.version += 1

        audit_service.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="property_updated",
            entity="property",
            entity_id=str(property_id),
            meta={"new_version": prop.version},
        )
        return prop

    def search_properties(
        self,
        tenant_id: uuid.UUID,
        query: str,
        category: str | None = None,
        threshold: float = 0.25,
        limit: int = 20,
    ) -> list[tuple[PropertyRecord, float]]:
        """Searches tenant properties using Devanagari and English trigram similarity."""
        from app.shared.trigram import trigram_similarity

        scored_matches: list[tuple[PropertyRecord, float]] = []
        for prop in self._properties.values():
            if prop.tenant_id != tenant_id or prop.deleted:
                continue
            if category and prop.category != category:
                continue

            candidates: list[str] = [prop.category]
            if isinstance(prop.attrs, dict):
                for v in prop.attrs.values():
                    if isinstance(v, (str, int, float)):
                        candidates.append(str(v))
            if isinstance(prop.boundaries, dict):
                for v in prop.boundaries.values():
                    if isinstance(v, str):
                        candidates.append(v)

            max_score = 0.0
            for cand in candidates:
                score = trigram_similarity(query, cand)
                if score > max_score:
                    max_score = score

            if max_score >= threshold:
                scored_matches.append((prop, round(max_score, 4)))

        scored_matches.sort(key=lambda x: x[1], reverse=True)
        return scored_matches[:limit]

    def reuse_property(
        self,
        property_id: uuid.UUID,
        tenant_id: uuid.UUID,
        overrides: dict[str, Any] | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> PropertyRecord:
        """Reuses property entity in a new matter (PRD FR-14, Features F-060).

        If overrides are provided, archives previous version snapshot and increments version,
        guaranteeing past documents generated with prior property data remain completely unchanged.
        """
        from dataclasses import asdict

        prop = self.get_property(property_id, tenant_id)
        if not prop:
            raise KeyError(f"Property {property_id} not found in tenant {tenant_id}")

        if overrides:
            # Archive current version
            self._versions.append(
                PropertyVersionRecord(
                    property_id=prop.id,
                    version=prop.version,
                    data=asdict(prop),
                    changed_by=actor_id,
                )
            )

            # Apply overrides
            if "attrs" in overrides and overrides["attrs"]:
                prop.attrs.update(overrides["attrs"])
            if "boundaries" in overrides and overrides["boundaries"]:
                prop.boundaries = overrides["boundaries"]
            if "area_value" in overrides and overrides["area_value"] is not None:
                prop.area_value = Decimal(str(overrides["area_value"]))
            if "area_unit" in overrides and overrides["area_unit"]:
                prop.area_unit = overrides["area_unit"]

            prop.version += 1

            audit_service.log_event(
                tenant_id=tenant_id,
                actor_id=actor_id,
                action="property_reused_with_updates",
                entity="property",
                entity_id=str(property_id),
                meta={"new_version": prop.version},
            )
        else:
            audit_service.log_event(
                tenant_id=tenant_id,
                actor_id=actor_id,
                action="property_reused",
                entity="property",
                entity_id=str(property_id),
                meta={"version": prop.version},
            )

        return prop

    def get_versions(self, property_id: uuid.UUID) -> list[PropertyVersionRecord]:
        return [v for v in self._versions if v.property_id == property_id]

    def clear(self) -> None:
        self._properties.clear()
        self._versions.clear()


property_service = PropertyService()

