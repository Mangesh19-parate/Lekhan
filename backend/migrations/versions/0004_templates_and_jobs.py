"""Templates, template versions, documents, jobs, and counters schema.

Revision ID: 0004_templates_and_jobs
Revises: 0003_entities_and_audit
Create Date: 2026-11-09 20:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_templates_and_jobs"
down_revision: Union[str, None] = "0003_entities_and_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. TEMPLATES Table
    op.create_table(
        "templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("doc_type", sa.String(length=64), nullable=False),
        sa.Column("property_category", sa.String(length=32), nullable=True),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "doc_type",
            "property_category",
            "language",
            "name",
            name="uq_templates_identity",
        ),
        sa.CheckConstraint("language IN ('mr','en','hi')", name="chk_template_language"),
    )

    # 2. TEMPLATE_VERSIONS Table
    op.create_table(
        "template_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("manifest_schema", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("compiled_ref", sa.String(length=512), nullable=True),
        sa.Column("file_ref", sa.String(length=512), nullable=False),
        sa.Column("file_sha256", sa.LargeBinary(length=32), nullable=False),
        sa.Column("lint_report", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column(
            "approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("template_id", "version", name="uq_template_version"),
        sa.CheckConstraint(
            "status IN ('draft','under_review','approved','retired')",
            name="chk_template_version_status",
        ),
        sa.CheckConstraint(
            "status <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)",
            name="chk_approved_requires_approver",
        ),
    )
    op.create_index("ix_template_versions_template_id", "template_versions", ["template_id"])

    # 3. DOCUMENTS Table
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "matter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matters.id"), nullable=True
        ),
        sa.Column(
            "template_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("template_versions.id"),
            nullable=False,
        ),
        sa.Column("engine_version", sa.String(length=32), server_default="0.1.0", nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("doc_no", sa.String(length=64), nullable=True),
        sa.Column("data_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("input_hash", sa.LargeBinary(length=32), nullable=True),
        sa.Column("output_hash", sa.LargeBinary(length=32), nullable=True),
        sa.Column("docx_ref", sa.String(length=512), nullable=True),
        sa.Column("pdf_ref", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("tenant_id", "doc_no", name="uq_documents_tenant_doc_no"),
        sa.CheckConstraint(
            "status IN ('draft','reviewed','finalised')", name="chk_document_status"
        ),
    )
    op.create_index(
        "ix_documents_tenant_matter", "documents", ["tenant_id", "matter_id", "created_at"]
    )
    op.create_index("ix_documents_tv", "documents", ["template_version_id"])

    # 4. JOBS Table (Postgres Queue for FOR UPDATE SKIP LOCKED)
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column("state", sa.String(length=64), nullable=True),
        sa.Column(
            "run_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_jobs_tenant_idempotency"),
        sa.CheckConstraint(
            "status IN ('queued','running','succeeded','failed','dead')", name="chk_job_status"
        ),
    )
    op.create_index(
        "ix_jobs_queue", "jobs", ["run_at"], postgresql_where=sa.text("status = 'queued'")
    )

    # 5. COUNTERS Table (Gap-free sequence numbering)
    op.create_table(
        "counters",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("value", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "key", "year", name="pk_counters"),
    )


def downgrade() -> None:
    op.drop_table("counters")
    op.drop_table("jobs")
    op.drop_table("documents")
    op.drop_table("template_versions")
    op.drop_table("templates")
