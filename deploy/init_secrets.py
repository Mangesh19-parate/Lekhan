"""Generates cryptographic secrets for production/staging Docker Compose deployments.

Adheres to:
- 32-byte cryptographically secure random values via secrets module
- Automatic initialization if deploy/secrets/ directory is missing
- Zero plain text secrets in source control (deploy/secrets/*.secret is ignored by git)
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
import secrets

SECRETS_DIR = Path(__file__).parent / "secrets"

SECRETS_CONFIG = {
    "db_password.secret": lambda: secrets.token_hex(24),
    "secret_key.secret": lambda: secrets.token_hex(32),
    "master_key.secret": lambda: base64.b64encode(secrets.token_bytes(32)).decode("ascii"),
    "index_key.secret": lambda: base64.b64encode(secrets.token_bytes(32)).decode("ascii"),
}


def init_secrets(overwrite: bool = False) -> None:
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    for fname, generator in SECRETS_CONFIG.items():
        secret_path = SECRETS_DIR / fname
        if not secret_path.exists() or overwrite:
            val = generator()
            secret_path.write_text(val.strip(), encoding="utf-8")
            print(f"[init_secrets] Generated {fname}")
        else:
            print(f"[init_secrets] {fname} already exists (skipping)")


if __name__ == "__main__":
    init_secrets()
