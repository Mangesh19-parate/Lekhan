"""Application configuration powered by Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Lekhan backend runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENV: Literal["dev", "test", "staging", "prod"] = "dev"
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://lekhan:lekhan@localhost:5432/lekhan_dev",
        description="SQLAlchemy PostgreSQL database connection string",
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

    # Storage and external binaries
    STORAGE_PATH: Path = Field(
        default=Path("./var/storage"),
        description="Local directory for generated documents and templates",
    )
    SOFFICE_BIN: str = Field(
        default="soffice",
        description="LibreOffice binary name or path",
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

    @property
    def is_dev(self) -> bool:
        """Indicates whether running in local development mode."""
        return self.ENV == "dev"

    @property
    def is_test(self) -> bool:
        """Indicates whether running under automated tests."""
        return self.ENV == "test"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns the cached singleton Settings instance."""
    return Settings()

