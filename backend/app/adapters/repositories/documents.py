"""PostgreSQL implementation of the DocumentRepository protocol.

Uses SQLAlchemy 2.0 Session to interact with the `documents` table.
Enforces strict tenant scoping on every method.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.adapters.db import SessionLocal
from app.generation.models import GeneratedDocumentRecord
from app.shared.models import Document as DocumentModel


def _to_record(model: DocumentModel) -> GeneratedDocumentRecord:
    """Converts a SQLAlchemy DocumentModel to domain GeneratedDocumentRecord."""
    return GeneratedDocumentRecord(
        id=model.id,
        tenant_id=model.tenant_id,
        template_version_id=model.template_version_id,
        doc_no=model.doc_no,
        engine_version=model.engine_version,
        language=model.language,
        data_snapshot=model.data_snapshot,
        input_hash=model.input_hash,
        output_hash=model.output_hash,
        file_ref=model.file_ref,
        pdf_ref=model.pdf_ref,
        status=model.status,
        created_at=model.created_at.isoformat() if model.created_at else "",
    )


class PostgresDocumentRepository:
    """Production PostgreSQL document repository implementing DocumentRepository."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def _get_session(self) -> Session:
        return self._session if self._session is not None else SessionLocal()

    def save(self, tenant_id: uuid.UUID, record: GeneratedDocumentRecord) -> None:
        if record.tenant_id != tenant_id:
            raise ValueError(f"Document tenant_id {record.tenant_id} does not match parameter {tenant_id}")

        session = self._get_session()
        should_close = self._session is None
        try:
            db_doc = DocumentModel(
                id=record.id,
                tenant_id=tenant_id,
                template_version_id=record.template_version_id,
                doc_no=record.doc_no,
                language=record.language,
                engine_version=record.engine_version,
                data_snapshot=record.data_snapshot,
                input_hash=record.input_hash,
                output_hash=record.output_hash,
                file_ref=record.file_ref,
                pdf_ref=record.pdf_ref,
                status=record.status,
            )
            session.add(db_doc)
            session.commit()
        finally:
            if should_close:
                session.close()

    def get(self, tenant_id: uuid.UUID, doc_id: uuid.UUID) -> GeneratedDocumentRecord | None:
        session = self._get_session()
        should_close = self._session is None
        try:
            db_doc = (
                session.query(DocumentModel)
                .filter(
                    DocumentModel.id == doc_id,
                    DocumentModel.tenant_id == tenant_id,
                )
                .first()
            )
            return _to_record(db_doc) if db_doc else None
        finally:
            if should_close:
                session.close()

    def update(self, tenant_id: uuid.UUID, record: GeneratedDocumentRecord) -> None:
        if record.tenant_id != tenant_id:
            raise ValueError(f"Document tenant_id {record.tenant_id} does not match parameter {tenant_id}")

        session = self._get_session()
        should_close = self._session is None
        try:
            db_doc = (
                session.query(DocumentModel)
                .filter(
                    DocumentModel.id == record.id,
                    DocumentModel.tenant_id == tenant_id,
                )
                .first()
            )
            if not db_doc:
                raise KeyError(f"Document {record.id} not found in tenant {tenant_id}")

            db_doc.status = record.status
            db_doc.file_ref = record.file_ref
            db_doc.pdf_ref = record.pdf_ref
            db_doc.output_hash = record.output_hash
            session.commit()
        finally:
            if should_close:
                session.close()

    def list(
        self,
        tenant_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[GeneratedDocumentRecord], int]:
        session = self._get_session()
        should_close = self._session is None
        try:
            query = session.query(DocumentModel).filter(DocumentModel.tenant_id == tenant_id)
            if status:
                query = query.filter(DocumentModel.status == status)
            if search:
                q = f"%{search.strip()}%"
                query = query.filter(DocumentModel.doc_no.ilike(q))

            total = query.count()
            db_docs = (
                query.order_by(DocumentModel.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [_to_record(d) for d in db_docs], total
        finally:
            if should_close:
                session.close()

