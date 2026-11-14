"""Party repository interfaces and in-memory test double.

Enforces:
- Explicit PartyRepository protocol.
- Every method takes tenant_id (AGENTS.md Hard Rule 6).
- Pure Python domain layer (no DB / ORM imports per AGENTS.md Section 3).
- InMemoryPartyRepository for test injection only.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from app.parties.models import PartyRecord, PartyVersionRecord
from app.shared.trigram import trigram_similarity


class PartyRepository(Protocol):
    """Explicit repository interface for party persistence."""

    def save(
        self,
        tenant_id: uuid.UUID,
        party: PartyRecord,
        actor_id: uuid.UUID | None = None,
    ) -> PartyRecord:
        """Persists a new party record within tenant_id."""
        ...

    def get(self, tenant_id: uuid.UUID, party_id: uuid.UUID) -> PartyRecord | None:
        """Retrieves a party record strictly scoped to tenant_id."""
        ...

    def update(
        self,
        tenant_id: uuid.UUID,
        party: PartyRecord,
        actor_id: uuid.UUID | None = None,
    ) -> PartyRecord:
        """Updates an existing party record within tenant_id."""
        ...

    def save_version(self, tenant_id: uuid.UUID, version: PartyVersionRecord) -> None:
        """Archives a historical version snapshot for a tenant party."""
        ...

    def get_versions(
        self,
        tenant_id: uuid.UUID | None,
        party_id: uuid.UUID,
    ) -> list[PartyVersionRecord]:
        """Returns all historical version records for a party."""
        ...

    def list_all(self, tenant_id: uuid.UUID) -> list[PartyRecord]:
        """Lists all active parties for tenant_id."""
        ...

    def search(
        self,
        tenant_id: uuid.UUID,
        query: str,
        threshold: float = 0.25,
        limit: int = 20,
    ) -> list[tuple[PartyRecord, float]]:
        """Searches tenant parties using trigram similarity."""
        ...


class InMemoryPartyRepository:
    """In-memory party repository for test injection only."""

    def __init__(self) -> None:
        self._parties: dict[uuid.UUID, PartyRecord] = {}
        self._versions: dict[uuid.UUID, list[PartyVersionRecord]] = {}

    def save(
        self,
        tenant_id: uuid.UUID,
        party: PartyRecord,
        actor_id: uuid.UUID | None = None,
    ) -> PartyRecord:
        if party.tenant_id != tenant_id:
            raise ValueError(f"Party tenant_id {party.tenant_id} does not match {tenant_id}")
        self._parties[party.id] = party
        return party

    def get(self, tenant_id: uuid.UUID, party_id: uuid.UUID) -> PartyRecord | None:
        party = self._parties.get(party_id)
        if not party or party.tenant_id != tenant_id or party.deleted:
            return None
        return party

    def update(
        self,
        tenant_id: uuid.UUID,
        party: PartyRecord,
        actor_id: uuid.UUID | None = None,
    ) -> PartyRecord:
        existing = self.get(tenant_id, party.id)
        if not existing:
            raise KeyError(f"Party {party.id} not found in tenant {tenant_id}")
        self._parties[party.id] = party
        return party

    def save_version(self, tenant_id: uuid.UUID, version: PartyVersionRecord) -> None:
        party = self.get(tenant_id, version.party_id)
        if not party:
            raise KeyError(f"Party {version.party_id} not found in tenant {tenant_id}")
        self._versions.setdefault(version.party_id, []).append(version)

    def get_versions(
        self,
        tenant_id: uuid.UUID | None,
        party_id: uuid.UUID,
    ) -> list[PartyVersionRecord]:
        if tenant_id is not None:
            party = self.get(tenant_id, party_id)
            if not party:
                return []
        return list(self._versions.get(party_id, []))

    def list_all(self, tenant_id: uuid.UUID) -> list[PartyRecord]:
        return [p for p in self._parties.values() if p.tenant_id == tenant_id and not p.deleted]

    def search(
        self,
        tenant_id: uuid.UUID,
        query: str,
        threshold: float = 0.25,
        limit: int = 20,
    ) -> list[tuple[PartyRecord, float]]:
        scored_matches: list[tuple[PartyRecord, float]] = []
        for party in self.list_all(tenant_id):
            candidates: list[str] = []
            if isinstance(party.names, dict):
                candidates.extend(str(v) for v in party.names.values() if v)
            if isinstance(party.addresses, dict):
                candidates.extend(str(v) for v in party.addresses.values() if v)
            if party.pan_masked:
                candidates.append(party.pan_masked)

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
                scored_matches.append((party, round(max_score, 4)))

        scored_matches.sort(key=lambda x: x[1], reverse=True)
        return scored_matches[:limit]

    def clear(self) -> None:
        self._parties.clear()
        self._versions.clear()
