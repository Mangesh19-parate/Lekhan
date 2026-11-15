"""Application configuration powered by Pydantic Settings."""

from __future__ import annotations

import base64
import binascii
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_KEY_PLACEHOLDERS = {
    "SECRET_KEY": "dev-insecure-secret-key-change-in-production-minimum-48-chars",
    "MASTER_KEY": "dev-master-key-32bytes-base64-placeholder==",
    "INDEX_KEY": "dev-index-key-32bytes-base64-placeholder==",
}


def _validate_deployed_key(name: str, value: str, require_base64_32bytes: bool = False) -> None:
    """Validates that a cryptographic key in staging/prod meets security requirements."""
    placeholder = _DEV_KEY_PLACEHOLDERS.get(name)
    if placeholder and value == placeholder:
        raise ValueError(f"{name} cannot be the default dev placeholder in staging/prod")

    lower_val = value.lower()
    if lower_val.startswith("change-me") or lower_val.startswith("dev-"):
        raise ValueError(f"{name} cannot start with 'change-me' or 'dev-' in staging/prod")

    if require_base64_32bytes:
        try:
            decoded = base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError) as err:
            raise ValueError(f"{name} must be valid base64 in staging/prod: {err}") from err
        if len(decoded) != 32:
            raise ValueError(
                f"{name} must be valid base64 of exactly 32 bytes in staging/prod (got {len(decoded)} bytes)"
            )
    else:
        # For SECRET_KEY: reject if shorter than 32 bytes decoded
        decoded_bytes: bytes
        try:
            decoded_bytes = base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError):
            decoded_bytes = value.encode("utf-8")
        if len(decoded_bytes) < 32:
            raise ValueError(
                f"{name} must be at least 32 bytes decoded in staging/prod (got {len(decoded_bytes)} bytes)"
            )


_SECRETS_DIR_PATH = Path(os.getenv("SECRETS_DIR", "/run/secrets"))
_ACTIVE_SECRETS_DIR = str(_SECRETS_DIR_PATH) if _SECRETS_DIR_PATH.is_dir() else None


class Settings(BaseSettings):
    """Lekhan backend runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        secrets_dir=_ACTIVE_SECRETS_DIR,
    )

    @model_validator(mode="before")
    @classmethod
    def _inject_docker_secrets(cls, data: Any) -> Any:
        """Injects file-based Docker secrets into configuration in production environments."""
        if isinstance(data, dict):
            secrets_dir = Path(os.getenv("SECRETS_DIR", "/run/secrets"))
            if secrets_dir.is_dir():
                for field in (
                    "secret_key",
                    "master_key",
                    "index_key",
                    "database_url",
                    "db_password",
                ):
                    secret_file = secrets_dir / field
                    if secret_file.is_file() and field.upper() not in data:
                        data[field.upper()] = secret_file.read_text(encoding="utf-8").strip()
                # If db_password secret exists and DATABASE_URL lacks credentials, inject it
                db_pw_file = secrets_dir / "db_password"
                if db_pw_file.is_file():
                    db_pw = db_pw_file.read_text(encoding="utf-8").strip()
                    db_url = data.get("DATABASE_URL", "")
                    if "lekhan@" in db_url and "lekhan:@" not in db_url:
                        data["DATABASE_URL"] = db_url.replace("lekhan@", f"lekhan:{db_pw}@")
                    elif "lekhan:lekhan@" in db_url:
                        data["DATABASE_URL"] = db_url.replace("lekhan:lekhan@", f"lekhan:{db_pw}@")
        return data

    ENV: Literal["dev", "test", "staging", "prod"] = "dev"
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://lekhan:lekhan@localhost:5432/lekhan_dev",
        description="SQLAlchemy PostgreSQL database connection string (owner/admin)",
    )
    APP_DATABASE_URL: str | None = Field(
        default=None,
        description="SQLAlchemy PostgreSQL connection string for non-privileged lekhan_app role",
    )

    # Cryptographic keys
    SECRET_KEY: str = Field(
        default="dev-insecure-secret-key-change-in-production-minimum-48-chars",
        description="Session cookie signing secret",
    )
    MASTER_KEY: str = Field(
        default="dev-master-key-32bytes-base64-placeholder==",
        description="Base64 encoded 32-byte key for AES-GCM field encryption",
    )
    INDEX_KEY: str = Field(
        default="dev-index-key-32bytes-base64-placeholder==",
        description="Base64 encoded 32-byte key for HMAC blind indexing",
    )
    ENFORCE_MFA: bool = Field(
        default=False,
        description="Enforce mandatory MFA for admin, reviewer, and template_admin roles",
    )

    # Storage and external binaries
    STORAGE_PATH: Path = Field(
        default=Path("./var/storage"),
        description="Local directory for generated documents and templates",
    )
    SOFFICE_BIN: str = Field(
        default="soffice",
        description="LibreOffice binary name or path",
    )
    LIBREOFFICE_PROCESS_LIMIT: int = Field(
        default=3,
        description="Maximum concurrent LibreOffice conversion processes",
    )
    LIBREOFFICE_TIMEOUT_SECONDS: float = Field(
        default=30.0,
        description="LibreOffice conversion timeout in seconds",
    )
    GENERATION_TIMEOUT_SECONDS: float = Field(
        default=60.0,
        description="Overall document generation timeout in seconds",
    )

    # CORS and Session Policy
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    SESSION_IDLE_MINUTES: int = 30
    SESSION_ABSOLUTE_HOURS: int = 12

    # Database Connection Pool Sizing (docs/ARCHITECTURE.md Section 8)
    DB_POOL_SIZE: int = Field(default=10, description="SQLAlchemy connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="SQLAlchemy pool max overflow connections")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Connection checkout timeout in seconds")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Connection recycling age in seconds")

    # Request Size Limits
    MAX_REQUEST_SIZE_BYTES: int = Field(
        default=10 * 1024 * 1024,
        description="Maximum HTTP request payload size in bytes (10 MB default)",
    )

    # Observability & Metrics Security
    METRICS_TOKEN: str | None = Field(
        default=None,
        description="Optional shared secret bearer token for /metrics endpoints",
    )
    METRICS_ALLOWED_IPS: list[str] = [
        "127.0.0.1",
        "::1",
        "localhost",
    ]
    TRUSTED_PROXIES: list[str] = [
        "127.0.0.1",
        "::1",
    ]

    @field_validator("ALLOWED_ORIGINS", "METRICS_ALLOWED_IPS", "TRUSTED_PROXIES", mode="before")
    @classmethod
    def _parse_list_from_str(cls, v: Any) -> list[str]:
        """Parses comma-separated strings or JSON arrays into list[str]."""
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in s.split(",") if item.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(item).strip() for item in v if str(item).strip()]
        return [str(v)] if v else []

    @property
    def is_dev(self) -> bool:
        """Indicates whether running in local development mode."""
        return self.ENV == "dev"

    @property
    def is_test(self) -> bool:
        """Indicates whether running under automated tests."""
        return self.ENV == "test"

    @model_validator(mode="after")
    def _reject_dev_keys_in_deployed_envs(self) -> "Settings":
        """Fail fast if staging/prod boots with placeholder dev cryptographic keys."""
        if self.ENV in ("staging", "prod"):
            _validate_deployed_key("SECRET_KEY", self.SECRET_KEY, require_base64_32bytes=False)
            _validate_deployed_key("MASTER_KEY", self.MASTER_KEY, require_base64_32bytes=True)
            _validate_deployed_key("INDEX_KEY", self.INDEX_KEY, require_base64_32bytes=True)
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns the cached singleton Settings instance."""
    return Settings()
