"""PostgreSQL End-to-End Drafting Lifecycle Integration Test (Finding 15 & Section 8 Step 8).

Verifies the complete real-database lifecycle against PostgreSQL 16:
1. Enqueue document generation job into PostgreSQL jobs queue with payload encryption.
2. Claim job cross-tenant via PostgreSQL `claim_next_job` SECURITY DEFINER function.
3. Process job through GenerationPipelineFSM:
   - Pinned approved template resolution.
   - Strict Jinja rendering and XML parts tag verification.
   - Atomic counter allocation in `counters` table within document transaction.
   - Persistence into `documents` table with authenticated AES-256-GCM data snapshot.
   - Chained SHA-256 entry in `audit_log`.
4. Review workflow via DocumentReviewService:
   - Queries PostgreSQL document.
   - Executes `mark_reviewed` and commits transaction.
5. Finalization workflow:
   - Verifies statutory checklist and executes `mark_finalised`.
   - Transitions document status to `finalised` with immutable lock.
6. Verification of audit log cryptographic integrity chain across tenant.
"""

from __future__ import annotations

import os
import uuid
from typing import Generator
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.adapters.db import current_tenant_id_ctx
from app.adapters.repositories.documents import PostgresDocumentRepository
from app.adapters.repositories.jobs import PostgresJobRepository
from app.adapters.storage import default_storage
from app.audit.jobs import verify_all_audit_chains
from app.audit.service import AuditService
from app.config import get_settings
from app.generation.pipeline import GenerationPipelineFSM
from app.review.fsm import DocumentFinalisedError, ReviewChecklist
from app.review.service import DocumentReviewService
from app.shared.models import (
    Base,
    Counter as CounterModel,
    Document as DocumentModel,
    DocumentReview as DocumentReviewModel,
    Job as JobModel,
    Tenant,
    User,
)
from app.shared.security import hash_password


VALID_LIFECYCLE_PAYLOAD = {
    "template_id": "sale_deed_plot_mr",
    "execution_date": "०९ नोव्हेंबर २०२६",
    "sellers": [
        {
            "full_name": "रमेश पाटील",
            "gender": "male",
            "age": 45,
            "occupation": "नोकरी",
            "address": "नागपूर",
            "pan": "ABCDE1234F",
        }
    ],
    "purchasers": [
        {
            "full_name": "सुनीता जोशी",
            "gender": "female",
            "age": 42,
            "occupation": "घरकाम",
            "address": "नागपूर",
            "pan": "XYZPQ9876K",
        }
    ],
    "property_details": {
        "mouza": "सोनेगाव",
        "khasra_no": "४५/२",
        "plot_no": "१२",
        "layout_name": "शिवकृपा लेआउट",
        "sheet_no": "१४",
        "area_sqm": 150.00,
    },
    "boundaries": {
        "east": "रस्ता",
        "west": "भूखंड क्र. १३",
        "north": "जागा",
        "south": "भूखंड क्र. ११",
    },
    "financial": {
        "total_consideration": 1550000.00,
        "earnest_advance": 200000.00,
        "instalments": [],
    },
    "witness_1": "१) साक्षीदार १",
    "witness_2": "२) साक्षीदार २",
}


@pytest.fixture(scope="module")
def postgres_session() -> Generator[Session, None, None]:
    """Connects to real PostgreSQL, initializes schema, and yields a test session."""
    settings = get_settings()
    db_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL") or settings.DATABASE_URL
    if "sqlite" in db_url:
        pytest.skip("PostgreSQL required for real PostgreSQL lifecycle test")

    engine = create_engine(db_url, connect_args={"connect_timeout": 2})
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostgreSQL unreachable: {exc}")
        return

    # Create schema tables if needed
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_full_real_postgres_drafting_lifecycle(postgres_session: Session) -> None:
    """Executes the complete legal document lifecycle against real PostgreSQL."""
    session = postgres_session
    tenant_id = uuid.uuid4()
    drafter_id = uuid.uuid4()
    reviewer_id = uuid.uuid4()

    # 1. Provision Tenant & Users
    tenant = Tenant(id=tenant_id, name="Lifecycle Law Chambers", slug=f"chamber-{tenant_id.hex[:6]}")
    session.add(tenant)

    drafter = User(
        id=drafter_id,
        tenant_id=tenant_id,
        email=f"drafter-{tenant_id.hex[:6]}@lekhan.local",
        display_name="Drafter Advocate",
        password_hash=hash_password("ValidPassword123!"),
        role="drafter",
        ui_language="mr",
    )
    reviewer = User(
        id=reviewer_id,
        tenant_id=tenant_id,
        email=f"reviewer-{tenant_id.hex[:6]}@lekhan.local",
        display_name="Senior Reviewer",
        password_hash=hash_password("ValidPassword123!"),
        role="reviewer",
        ui_language="mr",
    )
    session.add_all([drafter, reviewer])
    session.commit()

    # Set tenant context for RLS
    current_tenant_id_ctx.set(tenant_id)

    # 2. Enqueue document generation job into PostgreSQL jobs repository
    job_repo = PostgresJobRepository(session=session)
    job = job_repo.enqueue(
        tenant_id=tenant_id,
        type="generate_docx",
        payload=VALID_LIFECYCLE_PAYLOAD,
    )
    session.commit()

    assert job is not None
    assert job.status == "queued"

    # 3. Worker claims the job cross-tenant via claim_next
    claimed_job = job_repo.claim_next(tenant_id=None, visibility_timeout_seconds=300)
    assert claimed_job is not None
    assert claimed_job.id == job.id
    assert claimed_job.status == "running"

    # 4. Pipeline executes claimed job against PostgreSQL repositories
    doc_repo = PostgresDocumentRepository(session=session)
    pipeline = GenerationPipelineFSM(
        storage=default_storage,
        repository=doc_repo,
        db_session=session,
    )

    doc_record = pipeline.process_job(claimed_job)
    session.commit()

    # Verify generated document
    assert doc_record is not None
    assert doc_record.status == "draft"
    assert doc_record.doc_no is not None
    assert default_storage.exists(doc_record.file_ref) is True

    # Verify atomic counter persisted in PostgreSQL counters table
    counter_row = (
        session.query(CounterModel)
        .filter(CounterModel.tenant_id == tenant_id, CounterModel.key == "DOC")
        .first()
    )
    assert counter_row is not None
    assert counter_row.value >= 1

    # 5. Document Review: Reviewer marks document reviewed
    review_service = DocumentReviewService(pipeline=pipeline)
    checklist = ReviewChecklist(
        parties_verified=True,
        property_schedule_verified=True,
        consideration_and_payment_verified=True,
        no_unfilled_blanks=True,
        reviewer_notes="All boundaries and terms verified against registered 7/12 extract.",
    )
    review_rec = review_service.mark_reviewed(
        document_id=doc_record.id,
        tenant_id=tenant_id,
        checklist=checklist,
        reviewer_id=str(reviewer_id),
        session=session,
    )
    session.commit()

    assert review_rec is not None
    assert review_rec.reviewed_by == str(reviewer_id)

    # Check updated document status in DB
    refreshed_doc = doc_repo.get(tenant_id, doc_record.id)
    assert refreshed_doc is not None
    assert refreshed_doc.status == "reviewed"

    # 6. Document Finalization: Reviewer finalizes document with statutory checklist
    final_meta = review_service.mark_finalised(
        document_id=doc_record.id,
        tenant_id=tenant_id,
        finaliser_id=str(reviewer_id),
        session=session,
    )
    session.commit()

    assert final_meta is not None
    assert final_meta.status.value == "finalised"

    # 7. Document is now locked against modification
    with pytest.raises(DocumentFinalisedError, match="Finalised documents are immutable and cannot be re-reviewed."):
        review_service.mark_reviewed(
            document_id=doc_record.id,
            tenant_id=tenant_id,
            checklist=checklist,
            reviewer_id=str(reviewer_id),
            session=session,
        )

    # 8. Verify tamper-evident cryptographic audit chain integrity
    audit_report = verify_all_audit_chains()
    assert audit_report.status == "healthy"
    assert tenant_id not in audit_report.broken_tenants
