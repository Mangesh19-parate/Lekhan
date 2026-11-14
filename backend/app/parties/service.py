"""Parties domain service.

Features:
- Multi-lingual storage: names and addresses stored independently per script ('mr', 'en')
- Never auto-transliterated without user confirmation (AGENTS.md Domain Rules)
- Optimistic locking with automatic version snapshot archiving in party_versions
- Strictly tenant-scoped operations
- Explicit repository dependency injection
"""

from __future__ import annotations

import uuid
from dataclasses import asdict
from typing import Any

from app.audit.service import audit_service
from app.parties.models import PartyRecord, PartyVersionRecord
from app.parties.repository import InMemoryPartyRepository, PartyRepository
from app.shared.concurrency import OptimisticLockError
from app.shared.ids import uuid7
from app.shared.trigram import trigram_similarity


class PartyService:
    """Domain service for parties with version archiving."""

    def __init__(self, repository: PartyRepository | None = None) -> None:
        self.repository: PartyRepository = (
            repository if repository is not None else InMemoryPartyRepository()
        )

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
        saved = self.repository.save(tenant_id, party, actor_id=actor_id)

        # Audit event
        audit_service.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="party_created",
            entity="party",
            entity_id=str(party_id),
            meta={"kind": kind},
        )
        return saved

    def get_party(self, party_id: uuid.UUID, tenant_id: uuid.UUID) -> PartyRecord | None:
        """Retrieves a party strictly scoped to the requesting tenant."""
        return self.repository.get(tenant_id, party_id)

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
        self.repository.save_version(tenant_id, version_snapshot)

        # 3. Apply updates and increment version
        if names is not None:
            party.names = names
        if occupations is not None:
            party.occupations = occupations
        if addresses is not None:
            party.addresses = addresses

        party.version += 1
        updated = self.repository.update(tenant_id, party, actor_id=actor_id)

        # Audit event
        audit_service.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="party_updated",
            entity="party",
            entity_id=str(party_id),
            meta={"new_version": party.version},
        )
        return updated

    def get_versions(
        self, party_id: uuid.UUID, tenant_id: uuid.UUID | None = None
    ) -> list[PartyVersionRecord]:
        """Returns historical revisions for a party strictly within tenant_id."""
        return self.repository.get_versions(tenant_id, party_id)

    def search_parties(
        self,
        tenant_id: uuid.UUID,
        query: str,
        threshold: float = 0.25,
        limit: int = 20,
    ) -> list[tuple[PartyRecord, float]]:
        """Searches tenant parties using Devanagari and English trigram similarity."""
        return self.repository.search(
            tenant_id=tenant_id,
            query=query,
            threshold=threshold,
            limit=limit,
        )

    def reuse_party(
        self,
        party_id: uuid.UUID,
        tenant_id: uuid.UUID,
        overrides: dict[str, Any] | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> PartyRecord:
        """Reuses an existing party in a new matter (PRD FR-14, Features F-060)."""
        party = self.get_party(party_id, tenant_id)
        if not party:
            raise KeyError(f"Party {party_id} not found in tenant {tenant_id}")

        if overrides:
            version_snapshot = PartyVersionRecord(
                party_id=party.id,
                version=party.version,
                data=asdict(party),
                changed_by=actor_id,
            )
            self.repository.save_version(tenant_id, version_snapshot)

            if "names" in overrides and overrides["names"]:
                party.names = overrides["names"]
            if "addresses" in overrides and overrides["addresses"]:
                party.addresses = overrides["addresses"]
            if "occupations" in overrides and overrides["occupations"]:
                party.occupations = overrides["occupations"]
            if "age_or_dob" in overrides and overrides["age_or_dob"]:
                party.age_or_dob = overrides["age_or_dob"]

            party.version += 1
            updated = self.repository.update(tenant_id, party, actor_id=actor_id)

            audit_service.log_event(
                tenant_id=tenant_id,
                actor_id=actor_id,
                action="party_reused_with_updates",
                entity="party",
                entity_id=str(party_id),
                meta={"new_version": party.version},
            )
            return updated
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

    def detect_duplicates(
        self,
        tenant_id: uuid.UUID,
        name: str | None = None,
        pan: str | None = None,
        threshold: float = 0.85,
    ) -> list[dict[str, Any]]:
        """Detects potential duplicate parties based on exact PAN match or name trigram similarity."""
        parties = self.repository.list_all(tenant_id)
        duplicates: list[dict[str, Any]] = []

        for party in parties:
            if pan and party.pan_masked and pan.strip().upper() == party.pan_masked.strip().upper():
                duplicates.append(
                    {
                        "party_id": str(party.id),
                        "names": party.names,
                        "pan": party.pan_masked,
                        "match_type": "exact_pan",
                        "similarity": 1.0,
                        "reason": "Exact PAN match",
                    }
                )
                continue

            if name:
                names_to_check = list(party.names.values()) if isinstance(party.names, dict) else []
                for existing_name in names_to_check:
                    score = trigram_similarity(name, str(existing_name))
                    if score >= threshold:
                        duplicates.append(
                            {
                                "party_id": str(party.id),
                                "names": party.names,
                                "pan": party.pan_masked,
                                "match_type": "high_name_similarity",
                                "similarity": round(score, 4),
                                "reason": f"Devanagari/English name similarity {round(score * 100)}%",
                            }
                        )
                        break

        duplicates.sort(key=lambda x: x["similarity"], reverse=True)
        return duplicates

    def clear(self) -> None:
        """Clears repository data if the underlying repository supports clearing (test mode)."""
        if hasattr(self.repository, "clear"):
            self.repository.clear()


party_service = PartyService()
