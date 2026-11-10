"""Parties domain service.

Features:
- Multi-lingual storage: names and addresses stored independently per script ('mr', 'en')
- Never auto-transliterated without user confirmation (AGENTS.md Domain Rules)
- Optimistic locking with automatic version snapshot archiving in party_versions
- Strictly tenant-scoped operations
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from typing import Any

from app.audit.service import audit_service
from app.shared.concurrency import OptimisticLockError
from app.shared.ids import uuid7


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
    pan_masked: str | None
    version: int
    deleted: bool = False


@dataclass
class PartyVersionRecord:
    party_id: uuid.UUID
    version: int
    data: dict[str, Any]
    changed_by: uuid.UUID | None


class PartyService:
    """In-memory domain service for parties with version archiving."""

    def __init__(self) -> None:
        self._parties: dict[uuid.UUID, PartyRecord] = {}
        self._versions: list[PartyVersionRecord] = []

    def create_party(
        self,
        tenant_id: uuid.UUID,
        kind: str,
        names: dict[str, Any],
        gender: str | None = None,
        marital_status: str | None = None,
        age_or_dob: dict[str, Any] | None = None,
        occupations: dict[str, Any] | None = None,
        addresses: dict[str, Any] | None = None,
        pan_masked: str | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> PartyRecord:
        """Creates a new party record with initial version 1."""
        party_id = uuid7()
        party = PartyRecord(
            id=party_id,
            tenant_id=tenant_id,
            kind=kind,
            gender=gender,
            marital_status=marital_status,
            age_or_dob=age_or_dob,
            names=names,
            occupations=occupations or {},
            addresses=addresses or {},
            pan_masked=pan_masked,
            version=1,
        )
        self._parties[party_id] = party

        # Audit event
        audit_service.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="party_created",
            entity="party",
            entity_id=str(party_id),
            meta={"kind": kind},
        )
        return party

    def get_party(self, party_id: uuid.UUID, tenant_id: uuid.UUID) -> PartyRecord | None:
        """Retrieves a party strictly scoped to the requesting tenant."""
        party = self._parties.get(party_id)
        if not party or party.tenant_id != tenant_id or party.deleted:
            return None
        return party

    def update_party(
        self,
        party_id: uuid.UUID,
        tenant_id: uuid.UUID,
        expected_version: int,
        names: dict[str, Any] | None = None,
        occupations: dict[str, Any] | None = None,
        addresses: dict[str, Any] | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> PartyRecord:
        """Updates a party with optimistic locking.

        If expected_version != current_version, raises OptimisticLockError.
        Archives previous version snapshot into party_versions.
        """
        party = self.get_party(party_id, tenant_id)
        if not party:
            raise KeyError(f"Party {party_id} not found in tenant {tenant_id}")

        # 1. Optimistic Locking Check
        if party.version != expected_version:
            raise OptimisticLockError(
                f"Version conflict on party {party_id}: expected {expected_version}, but found {party.version}"
            )

        # 2. Archive current version snapshot
        version_snapshot = PartyVersionRecord(
            party_id=party.id,
            version=party.version,
            data=asdict(party),
            changed_by=actor_id,
        )
        self._versions.append(version_snapshot)

        # 3. Apply updates and increment version
        if names is not None:
            party.names = names
        if occupations is not None:
            party.occupations = occupations
        if addresses is not None:
            party.addresses = addresses

        party.version += 1

        # Audit event
        audit_service.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="party_updated",
            entity="party",
            entity_id=str(party_id),
            meta={"new_version": party.version},
        )
        return party

    def get_versions(self, party_id: uuid.UUID) -> list[PartyVersionRecord]:
        """Returns historical revisions for a party."""
        return [v for v in self._versions if v.party_id == party_id]

    def search_parties(
        self,
        tenant_id: uuid.UUID,
        query: str,
        threshold: float = 0.25,
        limit: int = 20,
    ) -> list[tuple[PartyRecord, float]]:
        """Searches tenant parties using Devanagari and English trigram similarity."""
        from app.shared.trigram import trigram_similarity

        scored_matches: list[tuple[PartyRecord, float]] = []
        for party in self._parties.values():
            if party.tenant_id != tenant_id or party.deleted:
                continue

            # Candidate search fields
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
                if score > max_score:
                    max_score = score

            if max_score >= threshold:
                scored_matches.append((party, round(max_score, 4)))

        # Sort descending by score
        scored_matches.sort(key=lambda x: x[1], reverse=True)
        return scored_matches[:limit]

    def reuse_party(
        self,
        party_id: uuid.UUID,
        tenant_id: uuid.UUID,
        overrides: dict[str, Any] | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> PartyRecord:
        """Reuses an existing party in a new matter (PRD FR-14, Features F-060).

        If overrides are provided, archives the previous version and increments the version counter,
        guaranteeing all prior generated matter documents remain completely untouched and immutable.
        """
        party = self.get_party(party_id, tenant_id)
        if not party:
            raise KeyError(f"Party {party_id} not found in tenant {tenant_id}")

        if overrides:
            # Archive current version
            version_snapshot = PartyVersionRecord(
                party_id=party.id,
                version=party.version,
                data=asdict(party),
                changed_by=actor_id,
            )
            self._versions.append(version_snapshot)

            # Apply overrides
            if "names" in overrides and overrides["names"]:
                party.names = overrides["names"]
            if "addresses" in overrides and overrides["addresses"]:
                party.addresses = overrides["addresses"]
            if "occupations" in overrides and overrides["occupations"]:
                party.occupations = overrides["occupations"]
            if "age_or_dob" in overrides and overrides["age_or_dob"]:
                party.age_or_dob = overrides["age_or_dob"]

            party.version += 1

            audit_service.log_event(
                tenant_id=tenant_id,
                actor_id=actor_id,
                action="party_reused_with_updates",
                entity="party",
                entity_id=str(party_id),
                meta={"new_version": party.version},
            )
        else:
            audit_service.log_event(
                tenant_id=tenant_id,
                actor_id=actor_id,
                action="party_reused",
                entity="party",
                entity_id=str(party_id),
                meta={"version": party.version},
            )

        return party

    def clear(self) -> None:
        self._parties.clear()
        self._versions.clear()


party_service = PartyService()

