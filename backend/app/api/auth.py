"""Authentication and session lifecycle endpoints (docs/API.md Section 2.1).

Implements:
- Argon2id password verification
- Session cookies (HttpOnly, Secure, SameSite=Lax)
- CSRF token validation
- Login throttling & account lockout (429 / 423)
- Session rotation on login and password changes
- Database-backed user repository & session repository (strictly tenant scoped)
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.adapters.db import get_db, set_tenant_context
from app.adapters.repositories.sessions import PostgresSessionRepository
from app.adapters.repositories.users import PostgresUserRepository
from app.config import get_settings
from app.identity.mfa import (
    build_otpauth_uri,
    generate_recovery_codes,
    generate_totp_secret,
    verify_and_consume_recovery_code,
    verify_totp_code,
)
from app.identity.models import UserRecord
from app.identity.policy import Actor
from app.identity.repository import UserRepository
from app.identity.service import (
    ABSOLUTE_TIMEOUT_HOURS,
    COOKIE_NAME,
    IDLE_TIMEOUT_MINUTES,
)
from app.identity.session_repository import SessionData, SessionRepository
from app.identity.throttling import login_throttler
from app.shared.logging import get_logger
from app.shared.security import (
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_csrf_token,
    verify_password,
)

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# --- Schemas ---


class LoginPayload(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)


class PasswordChangePayload(BaseModel):
    current_password: str
    new_password: str = Field(
        ..., min_length=12, description="Minimum 12 characters per docs/AUTH.md"
    )


class UserProfile(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    display_name: str
    role: str
    ui_language: str


class AuthResponse(BaseModel):
    user: UserProfile
    csrf_token: str


# --- Repository Dependencies ---


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    """Provides the UserRepository scoped to the current database session."""
    return PostgresUserRepository(db)


def get_session_repo(db: Session = Depends(get_db)) -> SessionRepository:
    """Provides the SessionRepository scoped to the current database session."""
    return PostgresSessionRepository(db)


# --- Dependencies ---


def get_current_actor(
    lekhan_session: str | None = Cookie(None, alias=COOKIE_NAME),
    session_repo: SessionRepository = Depends(get_session_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
) -> Actor:
    """Extracts and verifies the authenticated user from the session cookie."""
    if not lekhan_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing session cookie.",
        )

    id_hash = hash_token(lekhan_session)
    session_data = session_repo.find_by_hash(None, id_hash)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid.",
        )

    now = datetime.datetime.now(datetime.timezone.utc)

    # Check absolute timeout
    if now > session_data.expires_at:
        session_repo.delete(session_data.tenant_id, id_hash)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired.",
        )

    # Check sliding idle timeout (30 minutes)
    idle_limit = session_data.last_seen_at + datetime.timedelta(minutes=IDLE_TIMEOUT_MINUTES)
    if now > idle_limit:
        session_repo.delete(session_data.tenant_id, id_hash)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session idle timeout expired.",
        )

    # Refresh sliding window
    session_repo.touch(session_data.tenant_id, id_hash, now)

    # Locate user in identity store (strictly scoped to session tenant_id)
    user = user_repo.get_by_id(tenant_id=session_data.tenant_id, user_id=session_data.user_id)
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account inactive or not found.",
        )

    # Enforce Postgres row-level security context for downstream queries
    set_tenant_context(db, user.tenant_id)

    return Actor(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
        active=user.active,
    )


def require_csrf(
    request: Request,
    lekhan_session: str | None = Cookie(None, alias=COOKIE_NAME),
    x_csrf_token: str | None = Header(None, alias="X-CSRF-Token"),
    session_repo: SessionRepository = Depends(get_session_repo),
) -> None:
    """Enforces constant-time CSRF token validation on state-changing operations."""
    if not lekhan_session or not x_csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid.",
        )

    id_hash = hash_token(lekhan_session)
    session_data = session_repo.find_by_hash(None, id_hash)
    if not session_data or not verify_csrf_token(session_data.csrf_token_hash, x_csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token verification failed.",
        )


# --- Endpoints ---


@router.post("/login", response_model=AuthResponse, summary="User login")
def login(
    payload: LoginPayload,
    request: Request,
    response: Response,
    user_repo: UserRepository = Depends(get_user_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
) -> Any:
    """Authenticates credentials, enforces throttling, and rotates session cookie."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    throttle_key = f"{payload.email}:{client_ip}"

    # 1. Check rate-limit & lockout
    is_locked, remaining_seconds = login_throttler.is_locked(throttle_key)
    if is_locked:
        logger.warning("Throttled login attempt for %s from IP %s", payload.email, client_ip)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED
            if remaining_seconds > 60
            else status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to repeated failures. Retry in {remaining_seconds}s.",
            headers={"Retry-After": str(remaining_seconds)},
        )

    # 2. Lookup user and verify password
    user = user_repo.find_by_email(tenant_id=None, email=payload.email)
    if not user or not verify_password(user.password_hash, payload.password):
        locked_now, _ = login_throttler.record_failure(throttle_key)
        logger.info("Failed login attempt for %s", payload.email)
        if user:
            user_repo.record_failed_login(tenant_id=user.tenant_id, user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account inactive.",
        )

    # 3. Successful authentication: reset throttler
    login_throttler.record_success(throttle_key)
    user_repo.reset_failed_logins(tenant_id=user.tenant_id, user_id=user.id)

    # 4. Create fresh session (Session Rotation)
    user_agent = request.headers.get("User-Agent")
    session_token = generate_opaque_token(32)
    csrf_token = generate_opaque_token(32)

    id_hash = hash_token(session_token)
    csrf_hash = hash_token(csrf_token)

    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = now + datetime.timedelta(hours=ABSOLUTE_TIMEOUT_HOURS)

    session_data = SessionData(
        id_hash=id_hash,
        user_id=user.id,
        tenant_id=user.tenant_id,
        csrf_token_hash=csrf_hash,
        created_at=now,
        last_seen_at=now,
        expires_at=expires_at,
        user_agent=user_agent,
        ip=client_ip,
    )
    session_repo.save(tenant_id=user.tenant_id, session=session_data)

    # 5. Set HttpOnly, SameSite=Lax cookie
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=(not settings.is_dev),
        path="/",
    )

    profile = UserProfile(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        ui_language=user.ui_language,
    )
    return AuthResponse(user=profile, csrf_token=csrf_token)


@router.post("/logout", summary="User logout")
def logout(
    response: Response,
    lekhan_session: str | None = Cookie(None, alias=COOKIE_NAME),
    actor: Actor = Depends(get_current_actor),
    session_repo: SessionRepository = Depends(get_session_repo),
) -> dict[str, str]:
    """Destroys server session and clears cookie."""
    if lekhan_session:
        id_hash = hash_token(lekhan_session)
        session_repo.delete(tenant_id=actor.tenant_id, id_hash=id_hash)

    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/me", response_model=AuthResponse, summary="Current user profile")
def get_me(
    lekhan_session: str = Cookie(..., alias=COOKIE_NAME),
    actor: Actor = Depends(get_current_actor),
    user_repo: UserRepository = Depends(get_user_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
) -> AuthResponse:
    """Returns profile and active CSRF token for the current session."""
    user = user_repo.get_by_id(tenant_id=actor.tenant_id, user_id=actor.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    id_hash = hash_token(lekhan_session)
    session_data = session_repo.find_by_hash(tenant_id=actor.tenant_id, id_hash=id_hash)
    csrf_token = getattr(session_data, "raw_csrf_token", "active-csrf-token")
    profile = UserProfile(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        ui_language=user.ui_language,
    )
    return AuthResponse(user=profile, csrf_token=csrf_token)


@router.post("/password/change", summary="Change password")
def change_password(
    payload: PasswordChangePayload,
    response: Response,
    request: Request,
    lekhan_session: str = Cookie(..., alias=COOKIE_NAME),
    actor: Actor = Depends(get_current_actor),
    _csrf: None = Depends(require_csrf),
    user_repo: UserRepository = Depends(get_user_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
) -> dict[str, str]:
    """Updates password, invalidates all existing sessions, and rotates to a new session."""
    user = user_repo.get_by_id(tenant_id=actor.tenant_id, user_id=actor.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if not verify_password(user.password_hash, payload.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed.",
        )

    # 1. Update password hash
    user.password_hash = hash_password(payload.new_password)
    user_repo.update(tenant_id=actor.tenant_id, user=user)

    # 2. Revoke all prior sessions (docs/AUTH.md Section 2)
    session_repo.delete_all_for_user(tenant_id=actor.tenant_id, user_id=actor.user_id)

    # 3. Rotate session
    new_session_token = generate_opaque_token(32)
    new_csrf_token = generate_opaque_token(32)
    new_id_hash = hash_token(new_session_token)
    new_csrf_hash = hash_token(new_csrf_token)

    now = datetime.datetime.now(datetime.timezone.utc)
    new_expires_at = now + datetime.timedelta(hours=ABSOLUTE_TIMEOUT_HOURS)

    new_session_data = SessionData(
        id_hash=new_id_hash,
        user_id=actor.user_id,
        tenant_id=actor.tenant_id,
        csrf_token_hash=new_csrf_hash,
        created_at=now,
        last_seen_at=now,
        expires_at=new_expires_at,
        user_agent=request.headers.get("User-Agent"),
        ip=request.client.host if request.client else "127.0.0.1",
    )
    session_repo.save(tenant_id=actor.tenant_id, session=new_session_data)

    response.set_cookie(
        key=COOKIE_NAME,
        value=new_session_token,
        httponly=True,
        samesite="lax",
        secure=(not settings.is_dev),
        path="/",
    )

    return {"status": "ok", "message": "Password changed successfully"}


# --- Multi-Factor Authentication (MFA / TOTP) Endpoints (PRD FR-01, Features F-005) ---


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str
    recovery_codes: list[str]


class MfaEnablePayload(BaseModel):
    code: str


class MfaVerifyPayload(BaseModel):
    code: str | None = None
    recovery_code: str | None = None


# Ephemeral storage for MFA secrets pending enrollment verification
_PENDING_MFA_ENROLLMENTS: dict[uuid.UUID, dict[str, Any]] = {}


@router.post("/mfa/setup", response_model=MfaSetupResponse, summary="Initiate TOTP MFA setup")
def setup_mfa(
    actor: Actor = Depends(get_current_actor),
    user_repo: UserRepository = Depends(get_user_repo),
) -> Any:
    """Generates new TOTP base32 secret, otpauth:// URI, and 8 single-use recovery codes."""
    secret = generate_totp_secret()
    plain_recovery, hashed_recovery = generate_recovery_codes(count=8)

    user = user_repo.get_by_id(tenant_id=actor.tenant_id, user_id=actor.user_id)
    username = user.email if user else str(actor.user_id)
    otpauth_uri = build_otpauth_uri(secret=secret, username=username, issuer="Lekhan")

    _PENDING_MFA_ENROLLMENTS[actor.user_id] = {
        "secret": secret,
        "hashed_recovery_codes": hashed_recovery,
    }

    return MfaSetupResponse(
        secret=secret,
        otpauth_uri=otpauth_uri,
        recovery_codes=plain_recovery,
    )


@router.post("/mfa/enable", summary="Verify TOTP code and activate MFA")
def enable_mfa(
    payload: MfaEnablePayload,
    actor: Actor = Depends(get_current_actor),
    user_repo: UserRepository = Depends(get_user_repo),
) -> dict[str, Any]:
    """Verifies 6-digit TOTP code against pending secret and activates MFA."""
    pending = _PENDING_MFA_ENROLLMENTS.get(actor.user_id)
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending MFA setup found. Call /mfa/setup first.",
        )

    if not verify_totp_code(pending["secret"], payload.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 6-digit verification code. Please check your authenticator clock.",
        )

    user = user_repo.get_by_id(tenant_id=actor.tenant_id, user_id=actor.user_id)
    if user:
        user.mfa_secret_enc = pending["secret"].encode("utf-8")
        user_repo.update(tenant_id=actor.tenant_id, user=user)

    _PENDING_MFA_ENROLLMENTS.pop(actor.user_id, None)

    return {"status": "ok", "message": "Multi-Factor Authentication enabled successfully"}


@router.post("/mfa/verify", summary="Verify TOTP or recovery code")
def verify_mfa_login(
    payload: MfaVerifyPayload,
    actor: Actor = Depends(get_current_actor),
    user_repo: UserRepository = Depends(get_user_repo),
) -> dict[str, Any]:
    """Verifies a 6-digit TOTP code or consumes a one-time recovery code."""
    user = user_repo.get_by_id(tenant_id=actor.tenant_id, user_id=actor.user_id)
    if not user or not user.mfa_secret_enc:
        return {"status": "ok", "verified": True, "message": "MFA is not enabled for this user"}

    secret = user.mfa_secret_enc.decode("utf-8") if user.mfa_secret_enc else ""

    # 1. Try TOTP code
    if payload.code:
        if verify_totp_code(secret, payload.code):
            return {"status": "ok", "verified": True}

    # 2. Try recovery code
    if payload.recovery_code:
        stored_hashes = getattr(user, "mfa_recovery_codes", [])
        if verify_and_consume_recovery_code(payload.recovery_code, stored_hashes):
            return {
                "status": "ok",
                "verified": True,
                "recovery_code_used": True,
                "remaining_recovery_codes": len(stored_hashes),
            }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid MFA code or recovery code.",
    )


@router.post("/mfa/disable", summary="Disable MFA")
def disable_mfa(
    actor: Actor = Depends(get_current_actor),
    user_repo: UserRepository = Depends(get_user_repo),
) -> dict[str, Any]:
    """Disables MFA for the user."""
    user = user_repo.get_by_id(tenant_id=actor.tenant_id, user_id=actor.user_id)
    if user:
        user.mfa_secret_enc = None
        user_repo.update(tenant_id=actor.tenant_id, user=user)
    return {"status": "ok", "message": "MFA disabled"}
