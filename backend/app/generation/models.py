"""Generated document data records."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class GeneratedDocumentRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    template_version_id: uuid.UUID
    doc_no: str
    engine_version: str
    language: str
    data_snapshot: dict[str, Any]
    input_hash: bytes
    output_hash: bytes
    file_ref: str  # DOCX Master
    pdf_ref: str | None  # PDF Convenience Copy
    status: str  # draft, reviewed, finalised
    created_at: str  # ISO 8601
