"""Unit tests for runtime configuration."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from app.config import Settings, get_settings

VALID_SECRET = "a" * 64
VALID_MASTER = base64.b64encode(b"m" * 32).decode("ascii")
VALID_INDEX = base64.b64encode(b"i" * 32).decode("ascii")


def test_settings_defaults() -> None:
    """Verifies default settings configuration."""
    settings = get_settings()
    assert settings.ENV in ("dev", "test")
    assert "postgresql" in settings.DATABASE_URL
    assert settings.SESSION_IDLE_MINUTES == 30
    assert settings.SESSION_ABSOLUTE_HOURS == 12


def test_is_dev_and_is_test_flags() -> None:
    """Verifies environment convenience properties."""
    dev_settings = Settings(ENV="dev")
    assert dev_settings.is_dev is True
    assert dev_settings.is_test is False

    test_settings = Settings(ENV="test")
    assert test_settings.is_dev is False
    assert test_settings.is_test is True


def test_allowed_origins_parsing() -> None:
    """ALLOWED_ORIGINS parses comma-separated strings, JSON arrays, and lists."""
    # Comma-separated string
    s1 = Settings(ALLOWED_ORIGINS="http://localhost:5173, http://localhost:8000")  # type: ignore[arg-type]
    assert s1.ALLOWED_ORIGINS == ["http://localhost:5173", "http://localhost:8000"]

    # Single origin string (like .env.example)
    s2 = Settings(ALLOWED_ORIGINS="http://localhost:5173")  # type: ignore[arg-type]
    assert s2.ALLOWED_ORIGINS == ["http://localhost:5173"]

    # JSON list string
    s3 = Settings(ALLOWED_ORIGINS='["http://localhost:5173", "http://127.0.0.1:5173"]')  # type: ignore[arg-type]
    assert s3.ALLOWED_ORIGINS == ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Normal list
    s4 = Settings(ALLOWED_ORIGINS=["http://example.com"])
    assert s4.ALLOWED_ORIGINS == ["http://example.com"]


def test_dev_boot_with_env_example() -> None:
    """Dev boot with .env.example values succeeds without error."""
    env_example_path = Path(__file__).parent.parent.parent / ".env.example"
    assert env_example_path.exists(), f"{env_example_path} does not exist"

    # Load lines from .env.example into kwargs
    env_vars: dict[str, str] = {}
    for line in env_example_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip()

    # Settings must boot cleanly with .env.example variables
    settings = Settings(**env_vars)
    assert settings.ENV == "dev"
    assert settings.is_dev is True
    assert settings.ALLOWED_ORIGINS == ["http://localhost:5173"]
    assert settings.SECRET_KEY.startswith("change-me")


@pytest.mark.parametrize(
    ("bad_secret", "bad_master", "bad_index", "err_match"),
    [
        # Starts with change-me
        (
            "change-me-session-secret-longer-than-32-chars",
            VALID_MASTER,
            VALID_INDEX,
            "cannot start with 'change-me' or 'dev-'",
        ),
        (
            VALID_SECRET,
            "change-me-base64-placeholder-key-for-test==",
            VALID_INDEX,
            "cannot start with 'change-me' or 'dev-'",
        ),
        (
            VALID_SECRET,
            VALID_MASTER,
            "change-me-base64-placeholder-key-for-test==",
            "cannot start with 'change-me' or 'dev-'",
        ),
        # Starts with dev-
        (
            "dev-insecure-secret-key-that-is-long-enough-now",
            VALID_MASTER,
            VALID_INDEX,
            "cannot start with 'change-me' or 'dev-'",
        ),
        (
            VALID_SECRET,
            "dev-master-key-32bytes-base64-placeholder==",
            VALID_INDEX,
            "cannot be the default dev placeholder in staging/prod",
        ),
        (
            VALID_SECRET,
            VALID_MASTER,
            "dev-index-key-32bytes-base64-placeholder==",
            "cannot be the default dev placeholder in staging/prod",
        ),
        # Shorter than 32 bytes decoded
        (
            "too-short",
            VALID_MASTER,
            VALID_INDEX,
            "must be at least 32 bytes decoded",
        ),
        (
            base64.b64encode(b"short").decode("ascii"),
            VALID_MASTER,
            VALID_INDEX,
            "must be at least 32 bytes decoded",
        ),
        (
            VALID_SECRET,
            base64.b64encode(b"short").decode("ascii"),
            VALID_INDEX,
            "must be valid base64 of exactly 32 bytes",
        ),
        (
            VALID_SECRET,
            VALID_MASTER,
            base64.b64encode(b"short").decode("ascii"),
            "must be valid base64 of exactly 32 bytes",
        ),
        # Invalid base64 for MASTER_KEY / INDEX_KEY
        (
            VALID_SECRET,
            "this-is-not-valid-base64-and-has-dashes!!!",
            VALID_INDEX,
            "must be valid base64 in staging/prod",
        ),
        (
            VALID_SECRET,
            VALID_MASTER,
            "this-is-not-valid-base64-and-has-dashes!!!",
            "must be valid base64 in staging/prod",
        ),
        # Wrong decoded byte count (33 bytes) for MASTER_KEY / INDEX_KEY
        (
            VALID_SECRET,
            base64.b64encode(b"x" * 33).decode("ascii"),
            VALID_INDEX,
            "must be valid base64 of exactly 32 bytes",
        ),
        (
            VALID_SECRET,
            VALID_MASTER,
            base64.b64encode(b"x" * 33).decode("ascii"),
            "must be valid base64 of exactly 32 bytes",
        ),
    ],
)
def test_prod_boot_with_bad_keys_fails(
    bad_secret: str,
    bad_master: str,
    bad_index: str,
    err_match: str,
) -> None:
    """Staging and prod fail fast when any cryptographic key is insecure."""
    for env in ("staging", "prod"):
        with pytest.raises(ValueError, match=err_match):
            Settings(
                ENV=env,
                SECRET_KEY=bad_secret,
                MASTER_KEY=bad_master,
                INDEX_KEY=bad_index,
            )


def test_prod_boot_with_valid_keys_succeeds() -> None:
    """Prod boots successfully when all cryptographic keys satisfy requirements."""
    prod = Settings(
        ENV="prod",
        SECRET_KEY=VALID_SECRET,
        MASTER_KEY=VALID_MASTER,
        INDEX_KEY=VALID_INDEX,
    )
    assert prod.ENV == "prod"
    assert prod.is_dev is False
