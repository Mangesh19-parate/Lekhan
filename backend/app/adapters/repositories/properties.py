"""PostgreSQL implementation of the PropertyRepository protocol.

Uses SQLAlchemy 2.0 Session to interact with `properties` table.
Enforces strict tenant scoping on every method.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.adapters.db import SessionLocal
from app.properties.models import PropertyRecord, PropertyVersionRecord
from app.shared.models import Property as PropertyModel
from app.shared.trigram import trigram_similarity


def _to_record(model: PropertyModel) -> PropertyRecord:
    """Converts a SQLAlchemy PropertyModel to pure domain PropertyRecord."""
    return PropertyRecord(
        id=model.id,
        tenant_id=model.tenant_id,
        category=model.category,
        attrs=model.attrs,
        area_value=model.area_value,
        area_unit=model.area_unit,
        boundaries=model.boundaries,
        rr_division=model.rr_division,
        rr_rate=model.rr_rate,
        version=model.version,
    )


class PostgresPropertyRepository:
    """Production PostgreSQL property repository implementing PropertyRepository."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def _get_session(self) -> Session:
        return self._session if self._session is not None else SessionLocal()

    def save(
        self,
        tenant_id: uuid.UUID,
        prop: PropertyRecord,
        actor_id: uuid.UUID | None = None,
    ) -> PropertyRecord:
        if prop.tenant_id != tenant_id:
            raise ValueError(
                f"Property tenant_id {prop.tenant_id} does not match parameter {tenant_id}"
            )

        session = self._get_session()
        should_close = self._session is None
        try:
            db_prop = PropertyModel(
                id=prop.id,
                tenant_id=tenant_id,
                category=prop.category,
                attrs=prop.attrs,
                area_value=prop.area_value,
                area_unit=prop.area_unit,
                boundaries=prop.boundaries,
                rr_division=prop.rr_division,
                rr_rate=prop.rr_rate,
                version=prop.version,
            )
            session.add(db_prop)
            session.commit()
            return prop
        finally:
            if should_close:
                session.close()

    def get(self, tenant_id: uuid.UUID, property_id: uuid.UUID) -> PropertyRecord | None:
        session = self._get_session()
        should_close = self._session is None
        try:
            db_prop = (
                session.query(PropertyModel)
                .filter(
                    PropertyModel.id == property_id,
                    PropertyModel.tenant_id == tenant_id,
                    PropertyModel.deleted_at.is_(None),
                )
                .first()
            )
            return _to_record(db_prop) if db_prop else None
        finally:
            if should_close:
                session.close()

    def update(
        self,
        tenant_id: uuid.UUID,
        prop: PropertyRecord,
        actor_id: uuid.UUID | None = None,
    ) -> PropertyRecord:
        if prop.tenant_id != tenant_id:
            raise ValueError(
                f"Property tenant_id {prop.tenant_id} does not match parameter {tenant_id}"
            )

        session = self._get_session()
        should_close = self._session is None
        try:
            db_prop = (
                session.query(PropertyModel)
                .filter(
                    PropertyModel.id == prop.id,
                    PropertyModel.tenant_id == tenant_id,
                    PropertyModel.deleted_at.is_(None),
                )
                .first()
            )
            if not db_prop:
                raise KeyError(f"Property {prop.id} not found in tenant {tenant_id}")

            db_prop.attrs = prop.attrs
            db_prop.boundaries = prop.boundaries
            db_prop.version = prop.version
            session.commit()
            return prop
        finally:
            if should_close:
                session.close()

    def save_version(self, tenant_id: uuid.UUID, version: PropertyVersionRecord) -> None:
        # In-memory version tracking or future property_versions table
        pass

    def get_versions(
        self,
        tenant_id: uuid.UUID | None,
        property_id: uuid.UUID,
    ) -> list[PropertyVersionRecord]:
        return []

    def list_all(self, tenant_id: uuid.UUID) -> list[PropertyRecord]:
        session = self._get_session()
        should_close = self._session is None
        try:
            db_props = (
                session.query(PropertyModel)
                .filter(
                    PropertyModel.tenant_id == tenant_id,
                    PropertyModel.deleted_at.is_(None),
                )
                .all()
            )
            return [_to_record(p) for p in db_props]
        finally:
            if should_close:
                session.close()

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
