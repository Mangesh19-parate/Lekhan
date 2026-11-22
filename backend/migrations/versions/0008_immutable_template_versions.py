"""Make template versions immutable and DB-backed.

Revision ID: 0008_immutable_template_versions
Revises: 0007_rate_limits
Create Date: 2026-11-14 12:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_immutable_template_versions"
down_revision: Union[str, None] = "0007_rate_limits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns
    op.add_column(
        "template_versions",
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "template_versions",
        sa.Column("template_key", sa.String(length=64), server_default="", nullable=False),
    )
    op.add_column(
        "template_versions",
        sa.Column(
            "submitted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "template_versions",
        sa.Column(
            "manifest_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "template_versions",
        sa.Column("docx_sha256", sa.String(length=64), server_default="", nullable=False),
    )
    op.add_column(
        "template_versions",
        sa.Column("docx_ref", sa.String(length=512), server_default="", nullable=False),
    )

    # 2. Drop old constraints and indexes
    try:
        op.drop_constraint("uq_template_version", "template_versions", type_="unique")
    except Exception:
        pass
    try:
        op.drop_index("ix_template_versions_template_id", "template_versions")
    except Exception:
        pass

    # 3. Drop legacy columns
    for col in (
        "compiled_ref",
        "file_ref",
        "file_sha256",
        "lint_report",
        "manifest_schema",
        "manifest",
        "template_id",
    ):
        try:
            op.drop_column("template_versions", col)
        except Exception:
            pass

    # 4. Create new unique constraint and indexes
    op.create_unique_constraint(
        "uq_template_versions_key_version", "template_versions", ["template_key", "version"]
    )
    op.create_index("ix_template_versions_template_key", "template_versions", ["template_key"])
    op.create_index("ix_template_versions_tenant_id", "template_versions", ["tenant_id"])

    # 5. PostgreSQL Immutability Trigger
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION enforce_template_version_immutability()
            RETURNS TRIGGER AS $$
            BEGIN
                IF OLD.status = 'approved' THEN
                    IF NEW.status = 'retired'
                       AND NEW.template_key = OLD.template_key
                       AND NEW.version = OLD.version
                       AND NEW.docx_sha256 = OLD.docx_sha256
                       AND NEW.docx_ref = OLD.docx_ref
                       AND NEW.manifest_json = OLD.manifest_json
                       AND NEW.created_by = OLD.created_by
                       AND NEW.submitted_by = OLD.submitted_by
                       AND NEW.approved_by = OLD.approved_by
                       AND NEW.approved_at = OLD.approved_at THEN
                        RETURN NEW;
                    ELSE
                        RAISE EXCEPTION 'Approved template versions are immutable; only status transition to retired is allowed.';
                    END IF;
                END IF;

                IF OLD.status = 'retired' THEN
                    RAISE EXCEPTION 'Retired template versions cannot be updated.';
                END IF;

                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS trg_template_versions_immutable ON template_versions;
            CREATE TRIGGER trg_template_versions_immutable
            BEFORE UPDATE ON template_versions
            FOR EACH ROW
            EXECUTE FUNCTION enforce_template_version_immutability();
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_template_versions_immutable ON template_versions;")
        op.execute("DROP FUNCTION IF EXISTS enforce_template_version_immutability();")

    op.drop_index("ix_template_versions_tenant_id", "template_versions")
    op.drop_index("ix_template_versions_template_key", "template_versions")
    op.drop_constraint("uq_template_versions_key_version", "template_versions", type_="unique")

    for col in (
        "docx_ref",
        "docx_sha256",
        "manifest_json",
        "submitted_by",
        "template_key",
        "tenant_id",
    ):
        op.drop_column("template_versions", col)
