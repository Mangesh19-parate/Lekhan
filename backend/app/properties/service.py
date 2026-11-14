"""Properties domain service.

Features:
- Categorized real-estate entities (plots, flats, shops, agricultural land)
- Optimistic locking with automatic version snapshot archiving
- Strictly tenant-scoped operations
- Explicit repository dependency injection
"""

from __future__ import annotations

import uuid
from dataclasses import asdict
from decimal import Decimal
from typing import Any

from app.audit.service import audit_service
from app.properties.models import PropertyRecord, PropertyVersionRecord
from app.properties.repository import InMemoryPropertyRepository, PropertyRepository
from app.shared.concurrency import OptimisticLockError
from app.shared.ids import uuid7


class PropertyService:
    """Domain service for property entities."""

    def __init__(self, repository: PropertyRepository | None = None) -> None:
        self.repository: PropertyRepository = (
            repository if repository is not None else InMemoryPropertyRepository()
        )

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
        saved = self.repository.save(tenant_id, prop, actor_id=actor_id)

        audit_service.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="property_created",
            entity="property",
            entity_id=str(prop_id),
            meta={"category": category},
        )
        return saved

    def get_property(self, property_id: uuid.UUID, tenant_id: uuid.UUID) -> PropertyRecord | None:
        """Retrieves a property strictly scoped to tenant."""
        return self.repository.get(tenant_id, property_id)

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

        # Archive version snapshot
        version_snapshot = PropertyVersionRecord(
            property_id=prop.id,
            version=prop.version,
            data=asdict(prop),
            changed_by=actor_id,
        )
        self.repository.save_version(tenant_id, version_snapshot)

        if attrs is not None:
            prop.attrs = attrs
        if boundaries is not None:
            prop.boundaries = boundaries

        prop.version += 1
        updated = self.repository.update(tenant_id, prop, actor_id=actor_id)

        audit_service.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="property_updated",
            entity="property",
            entity_id=str(property_id),
            meta={"new_version": prop.version},
        )
        return updated

    def get_versions(
        self,
        property_id: uuid.UUID,
        tenant_id: uuid.UUID | None = None,
    ) -> list[PropertyVersionRecord]:
        """Returns historical revisions for a property."""
        return self.repository.get_versions(tenant_id, property_id)

    def search_properties(
        self,
        tenant_id: uuid.UUID,
        query: str,
        category: str | None = None,
        threshold: float = 0.25,
        limit: int = 20,
    ) -> list[tuple[PropertyRecord, float]]:
        """Searches tenant properties using trigram similarity."""
        return self.repository.search(
            tenant_id=tenant_id,
            query=query,
            category=category,
            threshold=threshold,
            limit=limit,
        )

    def reuse_property(
        self,
        property_id: uuid.UUID,
        tenant_id: uuid.UUID,
        overrides: dict[str, Any] | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> PropertyRecord:
        """Reuses an existing property entity, creating a version snapshot if modified."""
        prop = self.get_property(property_id, tenant_id)
        if not prop:
            raise KeyError(f"Property {property_id} not found in tenant {tenant_id}")

        if overrides:
            version_snapshot = PropertyVersionRecord(
                property_id=prop.id,
                version=prop.version,
                data=asdict(prop),
                changed_by=actor_id,
            )
            self.repository.save_version(tenant_id, version_snapshot)

            if "attrs" in overrides and overrides["attrs"]:
                prop.attrs = {**prop.attrs, **overrides["attrs"]}
            if "boundaries" in overrides and overrides["boundaries"]:
                prop.boundaries = overrides["boundaries"]

            prop.version += 1
            updated = self.repository.update(tenant_id, prop, actor_id=actor_id)

            audit_service.log_event(
                tenant_id=tenant_id,
                actor_id=actor_id,
                action="property_reused_with_updates",
                entity="property",
                entity_id=str(property_id),
                meta={"new_version": prop.version},
            )
            return updated
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

    def clear(self) -> None:
        """Clears repository data if the underlying repository supports clearing (test mode)."""
        if hasattr(self.repository, "clear"):
            self.repository.clear()


property_service = PropertyService()
