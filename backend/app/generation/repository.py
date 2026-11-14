"""Document repository interfaces and in-memory test double.

Enforces:
- Explicit DocumentRepository protocol.
- Every method takes tenant_id (AGENTS.md Hard Rule 6).
- Pure Python domain layer (no DB / ORM imports per AGENTS.md Section 3).
- InMemoryDocumentRepository for test injection only.
"""

from __future__ import annotations

import json
import uuid
from typing import Protocol, runtime_checkable

from app.generation.models import GeneratedDocumentRecord


@runtime_checkable
class DocumentRepository(Protocol):
    """Explicit repository interface for generated document persistence."""

    def save(self, tenant_id: uuid.UUID, record: GeneratedDocumentRecord) -> None:
        """Persists a generated document record within tenant_id."""
        ...

    def get(self, tenant_id: uuid.UUID, doc_id: uuid.UUID) -> GeneratedDocumentRecord | None:
        """Retrieves a document scoped strictly to tenant_id."""
        ...

    def update(self, tenant_id: uuid.UUID, record: GeneratedDocumentRecord) -> None:
        """Updates a document record within tenant_id."""
        ...

    def list(
        self,
        tenant_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[GeneratedDocumentRecord], int]:
        """Lists tenant documents with filtering, search, and pagination."""
        ...


class InMemoryDocumentRepository:
    """In-memory document repository for test injection only."""

    def __init__(self) -> None:
        self._documents: dict[uuid.UUID, GeneratedDocumentRecord] = {}

    def save(self, tenant_id: uuid.UUID, record: GeneratedDocumentRecord) -> None:
        if record.tenant_id != tenant_id:
            raise ValueError(f"Document tenant_id {record.tenant_id} does not match {tenant_id}")
        self._documents[record.id] = record

    def get(self, tenant_id: uuid.UUID, doc_id: uuid.UUID) -> GeneratedDocumentRecord | None:
        doc = self._documents.get(doc_id)
        if not doc or doc.tenant_id != tenant_id:
            return None
        return doc

    def update(self, tenant_id: uuid.UUID, record: GeneratedDocumentRecord) -> None:
        existing = self.get(tenant_id, record.id)
        if not existing:
            raise KeyError(f"Document {record.id} not found in tenant {tenant_id}")
        self._documents[record.id] = record

    def list(
        self,
        tenant_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[GeneratedDocumentRecord], int]:
        tenant_docs = [doc for doc in self._documents.values() if doc.tenant_id == tenant_id]
        if status:
            tenant_docs = [d for d in tenant_docs if d.status == status]
        if search:
            q = search.lower().strip()
            tenant_docs = [
                d
                for d in tenant_docs
                if q in d.doc_no.lower()
                or q in json.dumps(d.data_snapshot, ensure_ascii=False).lower()
            ]
        total = len(tenant_docs)
        return tenant_docs[offset : offset + limit], total

    def clear(self) -> None:
        self._documents.clear()
