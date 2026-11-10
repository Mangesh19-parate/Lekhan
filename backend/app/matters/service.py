"""Matters domain service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.audit.service import audit_service
from app.shared.ids import uuid7


@dataclass
class MatterRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    matter_no: str
    title: str | None
    status: str
    assigned_to: uuid.UUID | None
    created_by: uuid.UUID | None


@dataclass
class MatterPartyRecord:
    matter_id: uuid.UUID
    party_id: uuid.UUID
    role: str


class MatterService:
    """In-memory domain service for matters and associated parties."""

    def __init__(self) -> None:
        self._matters: dict[uuid.UUID, MatterRecord] = {}
        self._matter_parties: list[MatterPartyRecord] = []

    def create_matter(
        self,
        tenant_id: uuid.UUID,
        matter_no: str,
        title: str | None = None,
        assigned_to: uuid.UUID | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> MatterRecord:
        """Creates a new legal matter container."""
        # Uniqueness check per tenant
        for m in self._matters.values():
            if m.tenant_id == tenant_id and m.matter_no == matter_no:
                raise ValueError(f"Matter number '{matter_no}' already exists in this tenant.")

        matter_id = uuid7()
        matter = MatterRecord(
            id=matter_id,
            tenant_id=tenant_id,
            matter_no=matter_no,
            title=title,
            status="open",
            assigned_to=assigned_to,
            created_by=actor_id,
        )
        self._matters[matter_id] = matter

        audit_service.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="matter_created",
            entity="matter",
            entity_id=str(matter_id),
            meta={"matter_no": matter_no},
        )
        return matter

    def assign_party(
        self,
        matter_id: uuid.UUID,
        party_id: uuid.UUID,
        role: str,
    ) -> MatterPartyRecord:
        """Associates a party with a matter under a specific transaction role."""
        record = MatterPartyRecord(matter_id=matter_id, party_id=party_id, role=role)
        self._matter_parties.append(record)
        return record

    def get_matter_parties(self, matter_id: uuid.UUID) -> list[MatterPartyRecord]:
        """Returns all parties associated with a matter."""
        return [mp for mp in self._matter_parties if mp.matter_id == matter_id]

    def clear(self) -> None:
        self._matters.clear()
        self._matter_parties.clear()


matter_service = MatterService()

