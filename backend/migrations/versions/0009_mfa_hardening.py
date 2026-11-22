"""MFA hardening: recovery codes, mfa_pending sessions, and pending enrollments table.

Revision ID: 0009_mfa_hardening
Revises: 0008_immutable_template_versions
Create Date: 2026-11-14 12:47:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_mfa_hardening"
down_revision: Union[str, None] = "0008_immutable_template_versions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add mfa_recovery_codes to users
    op.add_column(
        "users",
        sa.Column(
            "mfa_recovery_codes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )

    # 2. Add mfa_pending to sessions
    op.add_column(
        "sessions",
        sa.Column(
            "mfa_pending",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    # 3. Create mfa_pending_enrollments table
    op.create_table(
        "mfa_pending_enrollments",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("secret_enc", sa.LargeBinary(), nullable=False),
        sa.Column(
            "hashed_recovery_codes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_mfa_pending_enrollments_expires_at",
        "mfa_pending_enrollments",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_mfa_pending_enrollments_expires_at", "mfa_pending_enrollments")
    op.drop_table("mfa_pending_enrollments")
    op.drop_column("sessions", "mfa_pending")
    op.drop_column("users", "mfa_recovery_codes")
