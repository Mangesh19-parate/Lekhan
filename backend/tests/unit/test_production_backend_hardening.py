"""Regression tests for production backend hardening and forensic security findings.

Verifies:
1. `set_tenant_context` strictly fails closed and raises on DB errors.
2. `get_db` cleans up ContextVar tokens using reset(token).
3. Production configuration validation: requires APP_DATABASE_URL, forbids matching DATABASE_URL, and forbids dev passwords.
4. Privacy-preserving rate-limit hashing: zero plaintext email/IP in rate_limits keys.
5. Zero-PII logging: no email or IP leaked during failed login attempts.
6. Logging formatter resilience: child loggers without correlation_id format safely.
7. Exact English monetary words-to-number inverse round-trip on large Indian scale values (> 1,000 Crore).
"""

from __future__ import annotations

import base64
import logging
import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.adapters.db import current_tenant_id_ctx, get_db, set_tenant_context
from app.api.auth import hash_rate_limit_key
from app.config import Settings
from app.lang_packs.english import number_to_words_en, words_to_number_en
from app.main import app
from app.shared.logging import CorrelationIdFormatter


def test_set_tenant_context_fails_closed_on_db_error() -> None:
    """Verifies set_tenant_context raises immediately if database execution fails (fail-closed)."""
    mock_session = MagicMock()
    mock_bind = MagicMock()
    mock_bind.dialect.name = "postgresql"
    mock_session.get_bind.return_value = mock_bind
    mock_session.execute.side_effect = OperationalError("connection reset", {}, None)

    test_tid = uuid.uuid4()
    with pytest.raises(OperationalError):
        set_tenant_context(mock_session, test_tid)


def test_set_tenant_context_sets_contextvar() -> None:
    """Verifies set_tenant_context updates current_tenant_id_ctx."""
    test_tid = uuid.uuid4()
    set_tenant_context(None, test_tid)
    assert current_tenant_id_ctx.get() == test_tid
    set_tenant_context(None, None)
    assert current_tenant_id_ctx.get() is None


def test_get_db_resets_contextvar_token() -> None:
    """Verifies get_db resets ContextVar token on exit."""
    parent_tid = uuid.uuid4()
    token = current_tenant_id_ctx.set(parent_tid)
    try:
        gen = get_db()
        _ = next(gen)
        # Inside get_db, context was reset to None
        assert current_tenant_id_ctx.get() is None
        try:
            next(gen)
        except StopIteration:
            pass
        # After get_db closes, parent context is restored
        assert current_tenant_id_ctx.get() == parent_tid
    finally:
        current_tenant_id_ctx.reset(token)


def test_production_config_rejects_missing_app_database_url() -> None:
    """Verifies Settings fails fast if APP_DATABASE_URL is missing in staging/prod."""
    valid_key = base64.b64encode(b"0" * 32).decode("ascii")
    with pytest.raises(ValueError, match="APP_DATABASE_URL is mandatory in staging/prod"):
        Settings(
            ENV="prod",
            DATABASE_URL="postgresql+psycopg://owner:secret@db.prod.internal:5432/lekhan_prod",
            APP_DATABASE_URL=None,
            SECRET_KEY=valid_key,
            MASTER_KEY=valid_key,
            INDEX_KEY=valid_key,
        )


def test_production_config_rejects_app_url_matching_owner_url() -> None:
    """Verifies Settings forbids APP_DATABASE_URL connecting with administrative database credentials."""
    valid_key = base64.b64encode(b"0" * 32).decode("ascii")
    same_url = "postgresql+psycopg://lekhan:supersecret@db.prod.internal:5432/lekhan_prod"
    with pytest.raises(ValueError, match="cannot match DATABASE_URL"):
        Settings(
            ENV="prod",
            DATABASE_URL=same_url,
            APP_DATABASE_URL=same_url,
            SECRET_KEY=valid_key,
            MASTER_KEY=valid_key,
            INDEX_KEY=valid_key,
        )


def test_production_config_rejects_dev_password_in_app_url() -> None:
    """Verifies Settings forbids default dev passwords in APP_DATABASE_URL in staging/prod."""
    valid_key = base64.b64encode(b"0" * 32).decode("ascii")
    dev_app_url = (
        "postgresql+psycopg://lekhan_app:lekhan_app_dev_password@db.prod.internal:5432/lekhan_prod"
    )
    with pytest.raises(ValueError, match="cannot use dev or placeholder credentials"):
        Settings(
            ENV="prod",
            DATABASE_URL="postgresql+psycopg://owner:supersecret@db.prod.internal:5432/lekhan_prod",
            APP_DATABASE_URL=dev_app_url,
            SECRET_KEY=valid_key,
            MASTER_KEY=valid_key,
            INDEX_KEY=valid_key,
        )


def test_privacy_preserving_rate_limit_keys() -> None:
    """Verifies hash_rate_limit_key emits fixed-length hashes without cleartext emails or IPs."""
    raw_email = "test.advocate.sharma@domain.co.in"
    raw_ip = "203.0.113.195"

    account_key = hash_rate_limit_key("account", raw_email)
    ip_key = hash_rate_limit_key("ip", raw_ip)

    assert "@" not in account_key
    assert "sharma" not in account_key
    assert account_key.startswith("account:")
    assert len(account_key) == 8 + 32  # "account:" + 32 hex chars

    assert raw_ip not in ip_key
    assert ip_key.startswith("ip:")
    assert len(ip_key) == 3 + 32  # "ip:" + 32 hex chars


def test_zero_pii_logging_during_failed_login(caplog: pytest.LogCaptureFixture) -> None:
    """Verifies failed login attempts never log email addresses or client IPs."""
    client = TestClient(app, raise_server_exceptions=False)
    raw_email = "confidential.client.secret@vidarbha-estates.com"

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": raw_email, "password": "wrong_password_attempt"},
            headers={"X-Forwarded-For": "198.51.100.42"},
        )

    assert response.status_code in (401, 500, 503)

    # Assert raw PII never appears in log messages
    for record in caplog.records:
        assert raw_email not in record.message
        assert "198.51.100.42" not in record.message
        assert "confidential" not in record.message


def test_correlation_id_formatter_with_foreign_loggers() -> None:
    """Verifies that foreign log records without correlation_id format safely without KeyError."""
    formatter = CorrelationIdFormatter(
        fmt="%(asctime)s [%(levelname)s] [cid:%(correlation_id)s] %(name)s: %(message)s"
    )
    foreign_record = logging.LogRecord(
        name="httpx",
        level=logging.INFO,
        pathname="/some/path.py",
        lineno=42,
        msg="HTTP Request: GET http://testserver/health/live",
        args=(),
        exc_info=None,
    )
    # Record has no correlation_id attribute initially
    assert not hasattr(foreign_record, "correlation_id")

    formatted = formatter.format(foreign_record)
    assert "[cid:-]" in formatted
    assert "HTTP Request:" in formatted


@pytest.mark.parametrize(
    "amount_str",
    [
        "10000000.00",  # 1 Crore
        "100000000.00",  # 10 Crore
        "1000000000.00",  # 100 Crore
        "10000000000.00",  # 1,000 Crore
        "15500000000.00",  # 1,550 Crore
        "50000000000.00",  # 5,000 Crore
        "100000000000.00",  # 10,000 Crore
        "1234567890123.45",  # > 1 Lakh Crore with paise
    ],
)
def test_large_indian_scale_words_to_number_roundtrip(amount_str: str) -> None:
    """Verifies mathematical inverse round-trip on large Indian scale values."""
    amount = Decimal(amount_str)
    words = number_to_words_en(amount, currency=True)
    parsed = words_to_number_en(words)
    assert parsed == amount, f"Failed roundtrip for {amount}: words='{words}', parsed='{parsed}'"
