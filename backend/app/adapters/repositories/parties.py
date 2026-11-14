"""PostgreSQL implementation of the PartyRepository protocol.

Uses SQLAlchemy 2.0 Session to interact with `parties` and `party_versions` tables.
Enforces strict tenant scoping on every method.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.adapters.db import SessionLocal
from app.parties.models import PartyRecord, PartyVersionRecord
from app.shared.models import Party as PartyModel
from app.shared.models import PartyVersion as PartyVersionModel
from app.shared.trigram import trigram_similarity


def _to_record(model: PartyModel) -> PartyRecord:
    """Converts a SQLAlchemy PartyModel to pure domain PartyRecord."""
    return PartyRecord(
        id=model.id,
        tenant_id=model.tenant_id,
        kind=model.kind,
        gender=model.gender,
        marital_status=model.marital_status,
        age_or_dob=model.age_or_dob,
        names=model.names,
        occupations=model.occupations,
        addresses=model.addresses,
        pan_masked=None,
        version=model.version,
    )


class PostgresPartyRepository:
    """Production PostgreSQL party repository implementing PartyRepository."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def _get_session(self) -> Session:
        return self._session if self._session is not None else SessionLocal()

    def save(
        self,
        tenant_id: uuid.UUID,
        party: PartyRecord,
        actor_id: uuid.UUID | None = None,
    ) -> PartyRecord:
        if party.tenant_id != tenant_id:
            raise ValueError(
                f"Party tenant_id {party.tenant_id} does not match parameter {tenant_id}"
            )

        session = self._get_session()
        should_close = self._session is None
        try:
            db_party = PartyModel(
                id=party.id,
                tenant_id=tenant_id,
                kind=party.kind,
                gender=party.gender,
                marital_status=party.marital_status,
                age_or_dob=party.age_or_dob,
                names=party.names,
                occupations=party.occupations,
                addresses=party.addresses,
                version=party.version,
                created_by=actor_id,
            )
            session.add(db_party)
            session.commit()
            return party
        finally:
            if should_close:
                session.close()

    def get(self, tenant_id: uuid.UUID, party_id: uuid.UUID) -> PartyRecord | None:
        session = self._get_session()
        should_close = self._session is None
        try:
            db_party = (
                session.query(PartyModel)
                .filter(
                    PartyModel.id == party_id,
                    PartyModel.tenant_id == tenant_id,
                    PartyModel.deleted_at.is_(None),
                )
                .first()
            )
            return _to_record(db_party) if db_party else None
        finally:
            if should_close:
                session.close()

    def update(
        self,
        tenant_id: uuid.UUID,
        party: PartyRecord,
        actor_id: uuid.UUID | None = None,
    ) -> PartyRecord:
        if party.tenant_id != tenant_id:
            raise ValueError(
                f"Party tenant_id {party.tenant_id} does not match parameter {tenant_id}"
            )

        session = self._get_session()
        should_close = self._session is None
        try:
            db_party = (
                session.query(PartyModel)
                .filter(
                    PartyModel.id == party.id,
                    PartyModel.tenant_id == tenant_id,
                    PartyModel.deleted_at.is_(None),
                )
                .first()
            )
            if not db_party:
                raise KeyError(f"Party {party.id} not found in tenant {tenant_id}")

            db_party.names = party.names
            db_party.occupations = party.occupations
            db_party.addresses = party.addresses
            db_party.version = party.version
            session.commit()
            return party
        finally:
            if should_close:
                session.close()

    def save_version(self, tenant_id: uuid.UUID, version: PartyVersionRecord) -> None:
        session = self._get_session()
        should_close = self._session is None
        try:
            # Verify party exists and is tenant-scoped
            db_party = (
                session.query(PartyModel)
                .filter(
                    PartyModel.id == version.party_id,
                    PartyModel.tenant_id == tenant_id,
                )
                .first()
            )
            if not db_party:
                raise KeyError(f"Party {version.party_id} not found in tenant {tenant_id}")

            db_ver = PartyVersionModel(
                party_id=version.party_id,
                version=version.version,
                data=version.data,
                changed_by=version.changed_by,
            )
            session.add(db_ver)
            session.commit()
        finally:
            if should_close:
                session.close()

    def get_versions(
        self,
        tenant_id: uuid.UUID | None,
        party_id: uuid.UUID,
    ) -> list[PartyVersionRecord]:
        session = self._get_session()
        should_close = self._session is None
        try:
            if tenant_id is not None:
                # Verify party exists under tenant
                db_party = (
                    session.query(PartyModel)
                    .filter(
                        PartyModel.id == party_id,
                        PartyModel.tenant_id == tenant_id,
                    )
                    .first()
                )
                if not db_party:
                    return []

            db_vers = (
                session.query(PartyVersionModel)
                .filter(PartyVersionModel.party_id == party_id)
                .order_by(PartyVersionModel.version.asc())
                .all()
            )
            return [
                PartyVersionRecord(
                    party_id=v.party_id,
                    version=v.version,
                    data=v.data,
                    changed_by=v.changed_by,
                )
                for v in db_vers
            ]
        finally:
            if should_close:
                session.close()

    def list_all(self, tenant_id: uuid.UUID) -> list[PartyRecord]:
        session = self._get_session()
        should_close = self._session is None
        try:
            db_parties = (
                session.query(PartyModel)
                .filter(
                    PartyModel.tenant_id == tenant_id,
                    PartyModel.deleted_at.is_(None),
                )
                .all()
            )
            return [_to_record(p) for p in db_parties]
        finally:
            if should_close:
                session.close()

    def search(
        self,
        tenant_id: uuid.UUID,
        query: str,
        threshold: float = 0.25,
        limit: int = 20,
    ) -> list[tuple[PartyRecord, float]]:
        parties = self.list_all(tenant_id)
        scored_matches: list[tuple[PartyRecord, float]] = []

        for party in parties:
            candidates: list[str] = []
            if isinstance(party.names, dict):
                candidates.extend(str(v) for v in party.names.values() if v)
            if isinstance(party.addresses, dict):
                candidates.extend(str(v) for v in party.addresses.values() if v)

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
