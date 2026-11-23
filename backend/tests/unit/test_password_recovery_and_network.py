"""Unit tests for Step 7: Password recovery delivery, MFA enforcement, and trusted proxy CIDR resolution."""

import uuid
from unittest.mock import MagicMock
import pytest
from starlette.datastructures import Headers

from app.api.auth import (
    ForgotPasswordPayload,
    ResetPasswordPayload,
    forgot_password,
    reset_password,
)
from app.config import Settings
from app.identity.models import UserRecord
from app.identity.repository import InMemoryUserRepository
from app.identity.session_repository import InMemorySessionRepository
from app.shared.network import get_client_ip
from app.shared.security import hash_password, verify_password


TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000000")
USER_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")


def _make_dummy_request(client_host: str = "127.0.0.1", headers: dict[str, str] | None = None):
    req = MagicMock()
    req.client.host = client_host
    req.headers = Headers(headers or {})
    return req


def test_forgot_and_reset_password_flow():
    """Verifies that forgot-password delivers a token and reset-password completes with it."""
    orig_password = "InitialPassword123!"
    user = UserRecord(
        id=USER_ID,
        tenant_id=TENANT_ID,
        email="drafter@lekhan.local",
        display_name="Advocate Drafter",
        password_hash=hash_password(orig_password),
        role="drafter",
        ui_language="mr",
    )
    user_repo = InMemoryUserRepository([user])
    session_repo = InMemorySessionRepository()

    # 1. Request password reset
    req1 = _make_dummy_request(client_host="10.0.0.1")
    forgot_payload = ForgotPasswordPayload(email="drafter@lekhan.local")
    forgot_res = forgot_password(forgot_payload, req1, user_repo=user_repo)

    assert forgot_res["status"] == "accepted"
    assert "reset_token" in forgot_res
    token = forgot_res["reset_token"]
    assert len(token) > 20

    # 2. Reset password using the delivered token
    new_password = "UpdatedNewPassword456!"
    reset_payload = ResetPasswordPayload(token=token, new_password=new_password)
    req2 = _make_dummy_request(client_host="10.0.0.2")
    reset_res = reset_password(
        reset_payload, req2, user_repo=user_repo, session_repo=session_repo
    )

    assert reset_res["status"] == "ok"

    # 3. Verify user record has updated password hash
    updated_user = user_repo.get_by_id(TENANT_ID, USER_ID)
    assert updated_user is not None
    assert verify_password(updated_user.password_hash, orig_password) is False
    assert verify_password(updated_user.password_hash, new_password) is True

    # 4. Token cannot be reused a second time (password hash prefix changed)
    with pytest.raises(Exception):
        reset_password(
            reset_payload, req2, user_repo=user_repo, session_repo=session_repo
        )


def test_forgot_password_user_enumeration_prevention():
    """Non-existent email returns 202 without leaking presence or returning a token."""
    user_repo = InMemoryUserRepository([])
    req = _make_dummy_request(client_host="10.0.0.3")
    forgot_payload = ForgotPasswordPayload(email="nonexistent@example.com")
    res = forgot_password(forgot_payload, req, user_repo=user_repo)

    assert res["status"] == "accepted"
    assert "reset_token" not in res


def test_proxy_trust_and_cidr_ip_resolution():
    """Verifies that client IP extraction honors trusted proxies including CIDR blocks and rejects untrusted."""
    trusted = ["127.0.0.1", "::1", "172.16.0.0/12", "10.0.0.0/8"]

    # 1. Loopback proxy
    req1 = _make_dummy_request("127.0.0.1", {"x-forwarded-for": "203.0.113.50, 10.0.0.1"})
    assert get_client_ip(req1, trusted_proxies=trusted) == "203.0.113.50"

    # 2. Docker container network proxy within 172.16.0.0/12
    req2 = _make_dummy_request("172.24.0.2", {"x-forwarded-for": "198.51.100.77"})
    assert get_client_ip(req2, trusted_proxies=trusted) == "198.51.100.77"

    # 3. Untrusted proxy peer: X-Forwarded-For must be completely ignored
    req3 = _make_dummy_request("198.51.100.99", {"x-forwarded-for": "203.0.113.1"})
    assert get_client_ip(req3, trusted_proxies=trusted) == "198.51.100.99"


def test_production_enforce_mfa_default():
    """In prod/staging environments, ENFORCE_MFA automatically defaults to True."""
    s = Settings(
        ENV="prod",
        SECRET_KEY="QUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUE=",
        MASTER_KEY="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        INDEX_KEY="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
    )
    assert s.ENFORCE_MFA is True
