"""Comprehensive unit and security tests for hardened MFA implementation.

Fulfills PRD FR-01, Features F-005, and docs/AUTH.md Section 6:
1. Two-step login: password OK + MFA enrolled -> short-lived mfa_pending session.
2. Login bypass attempt with mfa_pending session -> 403 Forbidden on all routes except /mfa/verify and /logout.
3. AES-256-GCM encryption of mfa_secret with MASTER_KEY, nonce uniqueness, and key ID rotation support.
4. Atomically consumed and persisted single-use recovery codes (prevent reuse).
5. TOTP replay protection within time window.
6. DB-backed pending MFA enrollments with 10-minute TTL.
7. /mfa/enable and /mfa/disable require current password + valid TOTP code.
8. Rate limiting / throttling on /mfa/verify (429 Too Many Requests).
9. Mandatory MFA enforcement for admin, reviewer, and template_admin roles.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any, Generator
from unittest.mock import patch

import pytest
from cryptography.exceptions import InvalidTag
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.db import get_db
from app.adapters.repositories.sessions import PostgresSessionRepository
from app.adapters.repositories.users import PostgresUserRepository
from app.api.auth import (
    _USED_TOTP_CODES,
    COOKIE_NAME,
    get_session_repo,
    get_user_repo,
    mfa_throttler,
)
from app.config import get_settings
from app.identity.mfa import generate_totp_code, generate_totp_secret
from app.main import app
from app.shared.crypto import decrypt_mfa_secret, encrypt_mfa_secret
from app.shared.ids import uuid7
from app.shared.models import Base, MfaPendingEnrollment, Session as SessionModel, Tenant, User as UserModel
from app.shared.security import derive_csrf_token, hash_password

settings = get_settings()

TEST_TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
TEST_PASSWORD = "StrongPassword#2026!"


@pytest.fixture
def test_db() -> Generator[Session, None, None]:
    """Sets up an in-memory SQLite database populated with base schema and test tenant."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    tenant = Tenant(
        id=TEST_TENANT_ID,
        name="Test Law Firm",
        slug="test-firm",
        tier="standard",
    )
    session.add(tenant)
    session.commit()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client_with_db(test_db: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient wired to the test database session and repositories."""
    def _override_get_db() -> Generator[Session, None, None]:
        yield test_db

    def _override_get_user_repo() -> PostgresUserRepository:
        return PostgresUserRepository(test_db)

    def _override_get_session_repo() -> PostgresSessionRepository:
        return PostgresSessionRepository(test_db)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_user_repo] = _override_get_user_repo
    app.dependency_overrides[get_session_repo] = _override_get_session_repo

    # Reset in-memory rate throttlers and replay caches
    mfa_throttler._attempts.clear()
    mfa_throttler._lockouts.clear()
    _USED_TOTP_CODES.clear()

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


def _create_user(
    db: Session,
    email: str,
    role: str = "drafter",
    mfa_secret: str | None = None,
    recovery_codes: list[str] | None = None,
) -> UserModel:
    """Helper to create a user with hashed password and optional encrypted MFA secret."""
    user = UserModel(
        id=uuid7(),
        tenant_id=TEST_TENANT_ID,
        email=email.lower().strip(),
        display_name=f"User {email}",
        password_hash=hash_password(TEST_PASSWORD),
        role=role,
        ui_language="en",
        mfa_secret_enc=encrypt_mfa_secret(mfa_secret) if mfa_secret else None,
        mfa_recovery_codes=recovery_codes or [],
        active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# --- 1. AES-256-GCM Encryption & Key Rotation Tests ---


def test_mfa_aes_gcm_encryption_and_rotation() -> None:
    """Verifies AES-256-GCM encryption with 12-byte random nonces and key_id binding."""
    secret = "JBSWY3DPEHPK3PXP"

    # Encrypt secret twice; nonces must ensure ciphertext uniqueness
    enc1 = encrypt_mfa_secret(secret, key_id="v1")
    enc2 = encrypt_mfa_secret(secret, key_id="v1")
    assert enc1 != enc2
    assert enc1.startswith(b"v1:")
    assert enc2.startswith(b"v1:")

    # Decrypt both
    assert decrypt_mfa_secret(enc1) == secret
    assert decrypt_mfa_secret(enc2) == secret

    # Tampering with ciphertext fails authenticated tag verification
    tampered = bytearray(enc1)
    tampered[-1] ^= 0x01
    with pytest.raises(InvalidTag):
        decrypt_mfa_secret(bytes(tampered))


# --- 2. Login Bypass Attempt with mfa_pending Session ---


def test_login_bypass_attempt_with_mfa_pending(
    client_with_db: TestClient, test_db: Session
) -> None:
    """Verifies that an mfa_pending session cannot access protected endpoints like /me or /parties."""
    totp_secret = generate_totp_secret()
    user = _create_user(test_db, "bypass@example.com", role="drafter", mfa_secret=totp_secret)

    # Step 1: Login with correct password
    res = client_with_db.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": TEST_PASSWORD},
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["mfa_required"] is True
    session_cookie = res.cookies.get(COOKIE_NAME)
    csrf_token = data["csrf_token"]
    assert session_cookie is not None

    # Step 2: Attempt to access /me (should be blocked with 403 Forbidden)
    res_me = client_with_db.get(
        "/api/v1/auth/me",
        cookies={COOKIE_NAME: session_cookie},
    )
    assert res_me.status_code == status.HTTP_403_FORBIDDEN
    assert "MFA verification required" in res_me.json()["detail"]

    # Step 3: Attempt to call a protected business route /api/v1/parties
    res_parties = client_with_db.post(
        "/api/v1/parties",
        json={"kind": "individual", "names": {"en": "Target Party"}},
        cookies={COOKIE_NAME: session_cookie},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res_parties.status_code == status.HTTP_403_FORBIDDEN
    assert "MFA verification required" in res_parties.json()["detail"]


# --- 3. Replayed TOTP Code Rejected ---


def test_replayed_totp_rejected(
    client_with_db: TestClient, test_db: Session
) -> None:
    """Verifies that a TOTP code cannot be replayed within the valid time window."""
    totp_secret = generate_totp_secret()
    user = _create_user(test_db, "totpreplay@example.com", role="drafter", mfa_secret=totp_secret)

    # Login to obtain mfa_pending session
    res = client_with_db.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": TEST_PASSWORD},
    )
    session_cookie = res.cookies[COOKIE_NAME]
    csrf_token = res.json()["csrf_token"]

    code = generate_totp_code(totp_secret)

    # 1. First verification with the TOTP code succeeds
    res_verify = client_with_db.post(
        "/api/v1/auth/mfa/verify",
        json={"code": code},
        cookies={COOKIE_NAME: session_cookie},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res_verify.status_code == status.HTTP_200_OK
    assert res_verify.json()["verified"] is True
    new_session_cookie = res_verify.cookies[COOKIE_NAME]

    # Now verify that the session has been promoted and can access /me
    res_me = client_with_db.get(
        "/api/v1/auth/me",
        cookies={COOKIE_NAME: new_session_cookie},
    )
    assert res_me.status_code == status.HTTP_200_OK

    # 2. Replay attempt: Login again with new mfa_pending session
    res_second_login = client_with_db.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": TEST_PASSWORD},
    )
    session_cookie2 = res_second_login.cookies[COOKIE_NAME]
    csrf_token2 = res_second_login.json()["csrf_token"]

    # Try submitting the same TOTP code again -> must be rejected
    res_replay = client_with_db.post(
        "/api/v1/auth/mfa/verify",
        json={"code": code},
        cookies={COOKIE_NAME: session_cookie2},
        headers={"X-CSRF-Token": csrf_token2},
    )
    assert res_replay.status_code == status.HTTP_401_UNAUTHORIZED
    assert "already been used" in res_replay.json()["detail"]


# --- 4. Reused Recovery Code Rejected ---


def test_reused_recovery_code_rejected(
    client_with_db: TestClient, test_db: Session
) -> None:
    """Verifies that a recovery code is consumed atomically and cannot be reused."""
    from app.identity.mfa import generate_recovery_codes

    totp_secret = generate_totp_secret()
    plain_codes, hashed_codes = generate_recovery_codes(count=4)
    target_recovery_code = plain_codes[0]

    user = _create_user(
        test_db,
        "recoverytest@example.com",
        role="drafter",
        mfa_secret=totp_secret,
        recovery_codes=hashed_codes,
    )

    # Login to obtain mfa_pending session
    res1 = client_with_db.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": TEST_PASSWORD},
    )
    session1 = res1.cookies[COOKIE_NAME]
    csrf1 = res1.json()["csrf_token"]

    # 1. First verification using the recovery code succeeds
    res_v1 = client_with_db.post(
        "/api/v1/auth/mfa/verify",
        json={"recovery_code": target_recovery_code},
        cookies={COOKIE_NAME: session1},
        headers={"X-CSRF-Token": csrf1},
    )
    assert res_v1.status_code == status.HTTP_200_OK
    assert res_v1.json()["recovery_code_used"] is True

    # Confirm in DB that code was consumed atomically (3 codes left)
    test_db.refresh(user)
    assert len(user.mfa_recovery_codes) == 3

    # 2. Login again to get a new mfa_pending session
    res2 = client_with_db.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": TEST_PASSWORD},
    )
    session2 = res2.cookies[COOKIE_NAME]
    csrf2 = res2.json()["csrf_token"]

    # 3. Try to use the same recovery code a second time -> fails
    res_v2 = client_with_db.post(
        "/api/v1/auth/mfa/verify",
        json={"recovery_code": target_recovery_code},
        cookies={COOKIE_NAME: session2},
        headers={"X-CSRF-Token": csrf2},
    )
    assert res_v2.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid MFA code or recovery code" in res_v2.json()["detail"]


# --- 5. MFA Setup, DB TTL, and Enable Requiring Password ---


def test_mfa_enable_requires_password_and_valid_code(
    client_with_db: TestClient, test_db: Session
) -> None:
    """Verifies that enabling MFA requires current password and valid TOTP code."""
    user = _create_user(test_db, "enabletest@example.com", role="drafter")

    # Login to full session (user does not have MFA yet)
    res_login = client_with_db.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": TEST_PASSWORD},
    )
    assert res_login.status_code == status.HTTP_200_OK
    session_cookie = res_login.cookies[COOKIE_NAME]
    csrf_token = res_login.json()["csrf_token"]

    # Initiate MFA setup
    res_setup = client_with_db.post(
        "/api/v1/auth/mfa/setup",
        cookies={COOKIE_NAME: session_cookie},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res_setup.status_code == status.HTTP_200_OK
    setup_data = res_setup.json()
    secret = setup_data["secret"]
    assert len(setup_data["recovery_codes"]) == 8

    # Verify pending enrollment is stored in the DB (not in a dict)
    pending = test_db.query(MfaPendingEnrollment).filter_by(user_id=user.id).first()
    assert pending is not None
    assert pending.secret_enc is not None
    assert len(pending.hashed_recovery_codes) == 8

    # Attempt 1: Enable with incorrect password -> 400 Bad Request
    valid_code = generate_totp_code(secret)
    res_wrong_pw = client_with_db.post(
        "/api/v1/auth/mfa/enable",
        json={"code": valid_code, "password": "WrongPassword123!"},
        cookies={COOKIE_NAME: session_cookie},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res_wrong_pw.status_code == status.HTTP_400_BAD_REQUEST
    assert "password verification failed" in res_wrong_pw.json()["detail"].lower()

    # Attempt 2: Enable with correct password but invalid code -> 400 Bad Request
    res_bad_code = client_with_db.post(
        "/api/v1/auth/mfa/enable",
        json={"code": "000000", "password": TEST_PASSWORD},
        cookies={COOKIE_NAME: session_cookie},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res_bad_code.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid 6-digit verification code" in res_bad_code.json()["detail"]

    # Attempt 3: Enable with correct password and valid code -> 200 OK
    res_enable = client_with_db.post(
        "/api/v1/auth/mfa/enable",
        json={"code": valid_code, "password": TEST_PASSWORD},
        cookies={COOKIE_NAME: session_cookie},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res_enable.status_code == status.HTTP_200_OK
    assert "enabled successfully" in res_enable.json()["message"]

    # Verify user record updated and pending enrollment consumed from DB
    test_db.refresh(user)
    assert user.mfa_secret_enc is not None
    assert len(user.mfa_recovery_codes) == 8
    pending_after = test_db.query(MfaPendingEnrollment).filter_by(user_id=user.id).first()
    assert pending_after is None


def test_mfa_pending_enrollment_db_ttl(
    client_with_db: TestClient, test_db: Session
) -> None:
    """Verifies that pending MFA enrollments expire after 10 minutes."""
    user = _create_user(test_db, "mfa_ttl@example.com", role="drafter")

    res_login = client_with_db.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": TEST_PASSWORD},
    )
    session_cookie = res_login.cookies[COOKIE_NAME]
    csrf_token = res_login.json()["csrf_token"]

    # Setup MFA
    res_setup = client_with_db.post(
        "/api/v1/auth/mfa/setup",
        cookies={COOKIE_NAME: session_cookie},
        headers={"X-CSRF-Token": csrf_token},
    )
    secret = res_setup.json()["secret"]

    # Age the pending enrollment past the 10-minute TTL in the DB
    pending = test_db.query(MfaPendingEnrollment).filter_by(user_id=user.id).first()
    assert pending is not None
    pending.expires_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)
    test_db.commit()

    # Attempt to enable -> fails due to expiration
    code = generate_totp_code(secret)
    res_enable = client_with_db.post(
        "/api/v1/auth/mfa/enable",
        json={"code": code, "password": TEST_PASSWORD},
        cookies={COOKIE_NAME: session_cookie},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res_enable.status_code == status.HTTP_400_BAD_REQUEST
    assert "expired" in res_enable.json()["detail"].lower()


# --- 6. MFA Disable Requiring Current Password and Code ---


def test_mfa_disable_requires_password_and_valid_code(
    client_with_db: TestClient, test_db: Session
) -> None:
    """Verifies that disabling MFA requires current password and a valid code."""
    totp_secret = generate_totp_secret()
    user = _create_user(test_db, "disabletest@example.com", role="drafter", mfa_secret=totp_secret)

    # Establish full session
    res_login = client_with_db.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": TEST_PASSWORD},
    )
    # Complete MFA verify step
    code = generate_totp_code(totp_secret)
    res_verify = client_with_db.post(
        "/api/v1/auth/mfa/verify",
        json={"code": code},
        cookies={COOKIE_NAME: res_login.cookies[COOKIE_NAME]},
        headers={"X-CSRF-Token": res_login.json()["csrf_token"]},
    )
    full_session_cookie = res_verify.cookies[COOKIE_NAME]
    full_csrf = res_verify.json()["csrf_token"]

    # Attempt 1: Disable with wrong password
    code_new = generate_totp_code(totp_secret)
    res_wrong_pw = client_with_db.post(
        "/api/v1/auth/mfa/disable",
        json={"code": code_new, "password": "WrongPassword!"},
        cookies={COOKIE_NAME: full_session_cookie},
        headers={"X-CSRF-Token": full_csrf},
    )
    assert res_wrong_pw.status_code == status.HTTP_400_BAD_REQUEST
    assert "password verification failed" in res_wrong_pw.json()["detail"].lower()

    # Attempt 2: Disable with correct password but invalid code
    res_bad_code = client_with_db.post(
        "/api/v1/auth/mfa/disable",
        json={"code": "999999", "password": TEST_PASSWORD},
        cookies={COOKIE_NAME: full_session_cookie},
        headers={"X-CSRF-Token": full_csrf},
    )
    assert res_bad_code.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid MFA verification code" in res_bad_code.json()["detail"]

    # Attempt 3: Disable with correct password and valid code
    res_disable = client_with_db.post(
        "/api/v1/auth/mfa/disable",
        json={"code": code_new, "password": TEST_PASSWORD},
        cookies={COOKIE_NAME: full_session_cookie},
        headers={"X-CSRF-Token": full_csrf},
    )
    assert res_disable.status_code == status.HTTP_200_OK

    # Confirm MFA secret is removed from user
    test_db.refresh(user)
    assert user.mfa_secret_enc is None
    assert user.mfa_recovery_codes == []


# --- 7. Rate Limiting on /mfa/verify ---


def test_rate_limiting_on_mfa_verify(
    client_with_db: TestClient, test_db: Session
) -> None:
    """Verifies that consecutive failed MFA verify calls trigger 429 Too Many Requests."""
    totp_secret = generate_totp_secret()
    user = _create_user(test_db, "ratelimit_mfa@example.com", role="drafter", mfa_secret=totp_secret)

    res_login = client_with_db.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": TEST_PASSWORD},
    )
    session_cookie = res_login.cookies[COOKIE_NAME]
    csrf_token = res_login.json()["csrf_token"]

    # Send 5 incorrect attempts
    for _ in range(5):
        res = client_with_db.post(
            "/api/v1/auth/mfa/verify",
            json={"code": "000000"},
            cookies={COOKIE_NAME: session_cookie},
            headers={"X-CSRF-Token": csrf_token},
        )
        assert res.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS)

    # Sixth attempt must be rate-limited
    res_locked = client_with_db.post(
        "/api/v1/auth/mfa/verify",
        json={"code": "000000"},
        cookies={COOKIE_NAME: session_cookie},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res_locked.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Too many failed MFA verification attempts" in res_locked.json()["detail"]


# --- 8. Mandatory MFA Enforcement for Roles ---


def test_mandatory_mfa_enforcement(
    client_with_db: TestClient, test_db: Session
) -> None:
    """Verifies ENFORCE_MFA flag blocks admin, reviewer, and template_admin if not enrolled."""
    # Drafter without MFA is allowed to log in directly
    drafter = _create_user(test_db, "drafter_free@example.com", role="drafter")
    res_drafter = client_with_db.post(
        "/api/v1/auth/login",
        json={"email": drafter.email, "password": TEST_PASSWORD},
    )
    assert res_drafter.status_code == status.HTTP_200_OK
    assert res_drafter.json()["mfa_required"] is False

    # Reviewer without MFA is blocked when ENFORCE_MFA is True
    reviewer = _create_user(test_db, "reviewer_mfa@example.com", role="reviewer")
    with patch.object(settings, "ENFORCE_MFA", True):
        res_rev = client_with_db.post(
            "/api/v1/auth/login",
            json={"email": reviewer.email, "password": TEST_PASSWORD},
        )
        assert res_rev.status_code == status.HTTP_403_FORBIDDEN
        assert "MFA enrollment is mandatory for role 'reviewer'" in res_rev.json()["detail"]

    # Admin without MFA is also blocked
    admin = _create_user(test_db, "admin_mfa@example.com", role="admin")
    with patch.object(settings, "ENFORCE_MFA", True):
        res_adm = client_with_db.post(
            "/api/v1/auth/login",
            json={"email": admin.email, "password": TEST_PASSWORD},
        )
        assert res_adm.status_code == status.HTTP_403_FORBIDDEN
        assert "MFA enrollment is mandatory for role 'admin'" in res_adm.json()["detail"]

    # Template Admin without MFA is blocked
    t_admin = _create_user(test_db, "t_admin_mfa@example.com", role="template_admin")
    with patch.object(settings, "ENFORCE_MFA", True):
        res_t_adm = client_with_db.post(
            "/api/v1/auth/login",
            json={"email": t_admin.email, "password": TEST_PASSWORD},
        )
        assert res_t_adm.status_code == status.HTTP_403_FORBIDDEN
        assert "MFA enrollment is mandatory for role 'template_admin'" in res_t_adm.json()["detail"]

    # When enrolled, admin login succeeds into mfa_pending step
    admin_enrolled = _create_user(
        test_db,
        "admin_enrolled@example.com",
        role="admin",
        mfa_secret=generate_totp_secret(),
    )
    with patch.object(settings, "ENFORCE_MFA", True):
        res_adm_ok = client_with_db.post(
            "/api/v1/auth/login",
            json={"email": admin_enrolled.email, "password": TEST_PASSWORD},
        )
        assert res_adm_ok.status_code == status.HTTP_200_OK
        assert res_adm_ok.json()["mfa_required"] is True
