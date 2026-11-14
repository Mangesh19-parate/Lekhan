"""Property repository interfaces and in-memory test double.

Enforces:
- Explicit PropertyRepository protocol.
- Every method takes tenant_id (AGENTS.md Hard Rule 6).
- Pure Python domain layer (no DB / ORM imports per AGENTS.md Section 3).
- InMemoryPropertyRepository for test injection only.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from app.properties.models import PropertyRecord, PropertyVersionRecord
from app.shared.trigram import trigram_similarity


class PropertyRepository(Protocol):
    """Explicit repository interface for property persistence."""

    def save(
        self,
        tenant_id: uuid.UUID,
        prop: PropertyRecord,
        actor_id: uuid.UUID | None = None,
    ) -> PropertyRecord:
        """Persists a new property record within tenant_id."""
        ...

    def get(self, tenant_id: uuid.UUID, property_id: uuid.UUID) -> PropertyRecord | None:
        """Retrieves a property record strictly scoped to tenant_id."""
        ...

    def update(
        self,
        tenant_id: uuid.UUID,
        prop: PropertyRecord,
        actor_id: uuid.UUID | None = None,
    ) -> PropertyRecord:
        """Updates an existing property record within tenant_id."""
        ...

    def save_version(self, tenant_id: uuid.UUID, version: PropertyVersionRecord) -> None:
        """Archives a historical property version snapshot within tenant_id."""
        ...

    def get_versions(
        self,
        tenant_id: uuid.UUID | None,
        property_id: uuid.UUID,
    ) -> list[PropertyVersionRecord]:
        """Returns all historical version records for a property."""
        ...

    def list_all(self, tenant_id: uuid.UUID) -> list[PropertyRecord]:
        """Lists all active properties for tenant_id."""
        ...

    def search(
        self,
        tenant_id: uuid.UUID,
        query: str,
        category: str | None = None,
        threshold: float = 0.25,
        limit: int = 20,
    ) -> list[tuple[PropertyRecord, float]]:
        """Searches tenant properties using trigram similarity."""
        ...


class InMemoryPropertyRepository:
    """In-memory property repository for test injection only."""

    def __init__(self) -> None:
        self._properties: dict[uuid.UUID, PropertyRecord] = {}
        self._versions: dict[uuid.UUID, list[PropertyVersionRecord]] = {}

    def save(
        self,
        tenant_id: uuid.UUID,
        prop: PropertyRecord,
        actor_id: uuid.UUID | None = None,
    ) -> PropertyRecord:
        if prop.tenant_id != tenant_id:
            raise ValueError(f"Property tenant_id {prop.tenant_id} does not match {tenant_id}")
        self._properties[prop.id] = prop
        return prop

    def get(self, tenant_id: uuid.UUID, property_id: uuid.UUID) -> PropertyRecord | None:
        prop = self._properties.get(property_id)
        if not prop or prop.tenant_id != tenant_id or prop.deleted:
            return None
        return prop

    def update(
        self,
        tenant_id: uuid.UUID,
        prop: PropertyRecord,
        actor_id: uuid.UUID | None = None,
    ) -> PropertyRecord:
        existing = self.get(tenant_id, prop.id)
        if not existing:
            raise KeyError(f"Property {prop.id} not found in tenant {tenant_id}")
        self._properties[prop.id] = prop
        return prop

    def save_version(self, tenant_id: uuid.UUID, version: PropertyVersionRecord) -> None:
        prop = self.get(tenant_id, version.property_id)
        if not prop:
            raise KeyError(f"Property {version.property_id} not found in tenant {tenant_id}")
        self._versions.setdefault(version.property_id, []).append(version)

    def get_versions(
        self,
        tenant_id: uuid.UUID | None,
        property_id: uuid.UUID,
    ) -> list[PropertyVersionRecord]:
        if tenant_id is not None:
            prop = self.get(tenant_id, property_id)
            if not prop:
                return []
        return list(self._versions.get(property_id, []))

    def list_all(self, tenant_id: uuid.UUID) -> list[PropertyRecord]:
        return [p for p in self._properties.values() if p.tenant_id == tenant_id and not p.deleted]

    def search(
        self,
        tenant_id: uuid.UUID,
        query: str,
        category: str | None = None,
        threshold: float = 0.25,
        limit: int = 20,
    ) -> list[tuple[PropertyRecord, float]]:
        props = self.list_all(tenant_id)
        if category:
            props = [p for p in props if p.category == category]

        scored_matches: list[tuple[PropertyRecord, float]] = []
        for prop in props:
            candidates: list[str] = []
            if isinstance(prop.attrs, dict):
                candidates.extend(str(v) for v in prop.attrs.values() if v)
            if isinstance(prop.boundaries, dict):
                candidates.extend(str(v) for v in prop.boundaries.values() if v)

            max_score = 0.0
            for cand in candidates:
                score = trigram_similarity(query, cand)
                for word in cand.split():
                    w_score = trigram_similarity(query, word)
                    if w_score > score:
                        score = w_score
                if score > max_score:
                    max_score = score

            if max_score >= threshold:
                scored_matches.append((prop, round(max_score, 4)))

        scored_matches.sort(key=lambda x: x[1], reverse=True)
        return scored_matches[:limit]

    def clear(self) -> None:
        self._properties.clear()
        self._versions.clear()
