"""Harden application role password provisioning and enforce strict production secrets.

Revision ID: 0015_harden_app_role_password
Revises: 0014_worker_job_claiming_function
Create Date: 2026-11-23 18:45:00.000000

"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence, Union

from alembic import op

revision: str = "0015_harden_app_role_password"
down_revision: Union[str, None] = "0014_worker_job_claiming_function"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enforces secure application role password in staging/prod and updates role password."""
    env = os.environ.get("ENV", "dev").lower()
    secrets_dir = Path(os.environ.get("SECRETS_DIR", "/run/secrets"))
    app_pw_file = secrets_dir / "app_db_password"

    app_password = None
    if app_pw_file.is_file():
        app_password = app_pw_file.read_text(encoding="utf-8").strip()
    elif "LEKHAN_APP_PASSWORD" in os.environ:
        app_password = os.environ["LEKHAN_APP_PASSWORD"].strip()

    if env in ("staging", "prod"):
        if not app_password:
            raise RuntimeError(
                "Production and staging migrations require an explicit, secure LEKHAN_APP_PASSWORD "
                "or app_db_password Docker secret. Running with default credentials is prohibited."
            )
        if (
            app_password == "lekhan_app_dev_password"
            or app_password.startswith("change-me")
            or app_password.startswith("dev-")
        ):
            raise RuntimeError(
                "Production and staging migrations cannot use default or placeholder credentials "
                "for the lekhan_app role."
            )

    if app_password:
        escaped_pw = app_password.replace("'", "''")
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'lekhan_app') THEN
                    EXECUTE format('ALTER ROLE lekhan_app WITH PASSWORD %L', '{escaped_pw}');
                END IF;
            END
            $$;
            """
        )


def downgrade() -> None:
    # Forward-only hardening; no-op downgrade preserves role password
    pass
