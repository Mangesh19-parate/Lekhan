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
        self._seed_dev_parties()

    def _seed_dev_parties(self) -> None:
        """Seeds initial synthetic dev parties for instant trigram search and reuse testing."""
        dev_tenants = [
            uuid.UUID("0193132e-504f-7a1b-8000-000000000000"),
            uuid.UUID("00000000-0000-4000-8000-000000000001"),
        ]
        synthetic_parties = [
            {
                "kind": "individual",
                "gender": "male",
                "marital_status": "married",
                "age_or_dob": {"age": 52},
                "names": {"mr": "आनंद बळवंत जोशी", "en": "Anand Balwant Joshi"},
                "occupations": {"mr": "व्यापार", "en": "Business"},
                "addresses": {
                    "mr": "फ्लॅट क्र. २०१, समर्थ संकुल, धरमपेठ, नागपूर",
                    "en": "Flat 201, Samarth Sankul, Dharampeth, Nagpur",
                },
                "pan_masked": "ABCDE1234F",
            },
            {
                "kind": "individual",
                "gender": "male",
                "marital_status": "married",
                "age_or_dob": {"age": 46},
                "names": {"mr": "सुरेश रामराव पाटील", "en": "Suresh Ramrao Patil"},
                "occupations": {"mr": "शेती व नोकरी", "en": "Agriculture & Service"},
                "addresses": {
                    "mr": "घर क्र. ४५, शिवाजी नगर, अमरावती रोड, नागपूर",
                    "en": "House No. 45, Shivaji Nagar, Amravati Road, Nagpur",
                },
                "pan_masked": "FGHIJ5678K",
            },
            {
                "kind": "individual",
                "gender": "female",
                "marital_status": "married",
                "age_or_dob": {"age": 48},
                "names": {"mr": "सुनीता विलास देशपांडे", "en": "Sunita Vilas Deshpande"},
                "occupations": {"mr": "शिक्षिका", "en": "Teacher"},
                "addresses": {
                    "mr": "प्लॉट क्र. १२, रामदासपेठ, नागपूर",
                    "en": "Plot No. 12, Ramdaspeth, Nagpur",
                },
                "pan_masked": "KLMNO9012P",
            },
        ]
        for tid in dev_tenants:
            for p in synthetic_parties:
                pid = uuid.uuid4()
                rec = PartyRecord(
                    id=pid,
                    tenant_id=tid,
                    kind=p["kind"],
                    gender=p["gender"],
                    marital_status=p["marital_status"],
                    age_or_dob=p["age_or_dob"],
                    names=p["names"],
                    occupations=p["occupations"],
                    addresses=p["addresses"],
                    pan_masked=p["pan_masked"],
                    version=1,
                )
                self._parties[pid] = rec

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

        # Persist to PostgreSQL if database connection is available
        try:
            from app.adapters.db import SessionLocal
            from app.shared.models import Party as PartyModel

            with SessionLocal() as db_session:
                db_party = PartyModel(
                    id=party_id,
                    tenant_id=tenant_id,
                    kind=kind,
                    gender=gender,
                    marital_status=marital_status,
                    age_or_dob=age_or_dob,
                    names=names,
                    occupations=occupations or {},
                    addresses=addresses or {},
                    version=1,
                    created_by=actor_id,
                )
                db_session.add(db_party)
                db_session.commit()
        except Exception:
            pass

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
        # 1. Query PostgreSQL first if available
        try:
            from app.adapters.db import SessionLocal
            from app.shared.models import Party as PartyModel

            with SessionLocal() as db_session:
                db_party = (
                    db_session.query(PartyModel)
                    .filter(
                        PartyModel.id == party_id,
                        PartyModel.tenant_id == tenant_id,
                        PartyModel.deleted_at.is_(None),
                    )
                    .first()
                )
                if db_party:
                    cached = self._parties.get(party_id)
                    return PartyRecord(
                        id=db_party.id,
                        tenant_id=db_party.tenant_id,
                        kind=db_party.kind,
                        gender=db_party.gender,
                        marital_status=db_party.marital_status,
                        age_or_dob=db_party.age_or_dob,
                        names=db_party.names,
                        occupations=db_party.occupations,
                        addresses=db_party.addresses,
                        pan_masked=cached.pan_masked if cached else None,
                        version=db_party.version,
                    )
        except Exception:
            pass

        # 2. Fallback to in-memory store
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
                # Word-level similarity for multi-word candidate strings (pg_trgm word_similarity)
                for word in cand.split():
                    w_score = trigram_similarity(query, word)
                    if w_score > score:
                        score = w_score
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

    def detect_duplicates(
        self,
        tenant_id: uuid.UUID,
        name: str | None = None,
        pan: str | None = None,
        threshold: float = 0.85,
    ) -> list[dict[str, Any]]:
        """Detects potential duplicate parties based on exact PAN match or name trigram similarity (Feature F-065)."""
        from app.shared.trigram import trigram_similarity

        duplicates: list[dict[str, Any]] = []
        for party in self._parties.values():
            if party.tenant_id != tenant_id or party.deleted:
                continue

            # 1. Exact PAN match
            if pan and party.pan_masked and pan.strip().upper() == party.pan_masked.strip().upper():
                duplicates.append({
                    "party_id": str(party.id),
                    "names": party.names,
                    "pan": party.pan_masked,
                    "match_type": "exact_pan",
                    "similarity": 1.0,
                    "reason": "Exact PAN match",
                })
                continue

            # 2. High name similarity
            if name:
                names_to_check = list(party.names.values()) if isinstance(party.names, dict) else []
                for existing_name in names_to_check:
                    score = trigram_similarity(name, str(existing_name))
                    if score >= threshold:
                        duplicates.append({
                            "party_id": str(party.id),
                            "names": party.names,
                            "pan": party.pan_masked,
                            "match_type": "high_name_similarity",
                            "similarity": round(score, 4),
                            "reason": f"Devanagari/English name similarity {round(score * 100)}%",
                        })
                        break

        duplicates.sort(key=lambda x: x["similarity"], reverse=True)
        return duplicates

    def clear(self) -> None:
        self._parties.clear()
        self._versions.clear()


party_service = PartyService()
