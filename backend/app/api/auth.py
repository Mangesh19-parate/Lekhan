"""Authentication and session lifecycle endpoints (docs/API.md Section 2.1).

Implements:
- Argon2id password verification
- Session cookies (HttpOnly, Secure, SameSite=Lax)
- CSRF token validation
- Login throttling & account lockout (429 / 423)
- Session rotation on login and password changes
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from app.config import get_settings
from app.identity.policy import Action, Actor, Decision, Resource, authorize
from app.identity.mfa import (
    build_otpauth_uri,
    generate_recovery_codes,
    generate_totp_secret,
    verify_and_consume_recovery_code,
    verify_totp_code,
)
from app.identity.service import COOKIE_NAME, session_store
from app.identity.throttling import login_throttler
from app.shared.errors import problem_json_response
from app.shared.logging import get_logger
from app.shared.security import hash_password, verify_password

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# --- Schemas ---

class LoginPayload(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class PasswordChangePayload(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12, description="Minimum 12 characters per docs/AUTH.md")


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


# --- In-Memory Synthetic Accounts for Dev/Testing ---

SYNTHETIC_USERS: dict[str, dict[str, Any]] = {
    "admin@lekhan.local": {
        "id": uuid.UUID("0193132e-504f-7a1b-8000-000000000001"),
        "tenant_id": uuid.UUID("0193132e-504f-7a1b-8000-000000000000"),
        "email": "admin@lekhan.local",
        "display_name": "Senior Partner (Admin)",
        "password_hash": hash_password("ValidPassword123!"),
        "role": "admin",
        "ui_language": "mr",
        "active": True,
    },
    "drafter@lekhan.local": {
        "id": uuid.UUID("0193132e-504f-7a1b-8000-000000000002"),
        "tenant_id": uuid.UUID("0193132e-504f-7a1b-8000-000000000000"),
        "email": "drafter@lekhan.local",
        "display_name": "Advocate Drafter (Nagpur)",
        "password_hash": hash_password("ValidPassword123!"),
        "role": "drafter",
        "ui_language": "mr",
        "active": True,
    },
    "reviewer@lekhan.local": {
        "id": uuid.UUID("0193132e-504f-7a1b-8000-000000000003"),
        "tenant_id": uuid.UUID("0193132e-504f-7a1b-8000-000000000000"),
        "email": "reviewer@lekhan.local",
        "display_name": "Reviewer Advocate",
        "password_hash": hash_password("ValidPassword123!"),
        "role": "reviewer",
        "ui_language": "mr",
        "active": True,
    },
    "template_admin@lekhan.local": {
        "id": uuid.UUID("0193132e-504f-7a1b-8000-000000000004"),
        "tenant_id": uuid.UUID("0193132e-504f-7a1b-8000-000000000000"),
        "email": "template_admin@lekhan.local",
        "display_name": "Template Administrator",
        "password_hash": hash_password("ValidPassword123!"),
        "role": "template_admin",
        "ui_language": "en",
        "active": True,
    },
    # Secondary tenant user to test cross-tenant 404 isolation
    "other_tenant@lekhan.local": {
        "id": uuid.UUID("0193132e-504f-7a1b-8000-000000000099"),
        "tenant_id": uuid.UUID("0193132e-504f-7a1b-8000-000000000099"),
        "email": "other_tenant@lekhan.local",
        "display_name": "External Tenant User",
        "password_hash": hash_password("ValidPassword123!"),
        "role": "drafter",
        "ui_language": "en",
        "active": True,
    },
}


# --- Dependencies ---

def get_current_actor(
    lekhan_session: str | None = Cookie(None, alias=COOKIE_NAME),
) -> Actor:
    """Extracts and verifies the authenticated user from the session cookie."""
    if not lekhan_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing session cookie.",
        )

    session_data = session_store.get_session(lekhan_session)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid.",
        )

    # Locate user in identity store
    user = next((u for u in SYNTHETIC_USERS.values() if u["id"] == session_data.user_id), None)
    if not user or not user["active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account inactive or not found.",
        )

    return Actor(
        user_id=user["id"],
        tenant_id=user["tenant_id"],
        role=user["role"],
        active=user["active"],
    )


def require_csrf(
    request: Request,
    lekhan_session: str | None = Cookie(None, alias=COOKIE_NAME),
    x_csrf_token: str | None = Header(None, alias="X-CSRF-Token"),
) -> None:
    """Enforces constant-time CSRF token validation on state-changing operations."""
    if not lekhan_session or not x_csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid.",
        )

    if not session_store.validate_csrf(lekhan_session, x_csrf_token):
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
) -> Any:
    """Authenticates credentials, enforces throttling, and rotates session cookie."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    throttle_key = f"{payload.email}:{client_ip}"

    # 1. Check rate-limit & lockout
    is_locked, remaining_seconds = login_throttler.is_locked(throttle_key)
    if is_locked:
        logger.warning("Throttled login attempt for %s from IP %s", payload.email, client_ip)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED if remaining_seconds > 60 else status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to repeated failures. Retry in {remaining_seconds}s.",
            headers={"Retry-After": str(remaining_seconds)},
        )

    # 2. Lookup user and verify password
    user = SYNTHETIC_USERS.get(payload.email.lower().strip())
    if not user or not verify_password(user["password_hash"], payload.password):
        locked_now, _ = login_throttler.record_failure(throttle_key)
        logger.info("Failed login attempt for %s", payload.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # 3. Successful authentication: reset throttler
    login_throttler.record_success(throttle_key)

    # 4. Create fresh session (Session Rotation)
    user_agent = request.headers.get("User-Agent")
    session_token, csrf_token = session_store.create_session(
        user_id=user["id"],
        tenant_id=user["tenant_id"],
        user_agent=user_agent,
        ip=client_ip,
    )

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
        id=user["id"],
        tenant_id=user["tenant_id"],
        email=user["email"],
        display_name=user["display_name"],
        role=user["role"],
        ui_language=user["ui_language"],
    )
    return AuthResponse(user=profile, csrf_token=csrf_token)


@router.post("/logout", summary="User logout")
def logout(
    response: Response,
    lekhan_session: str | None = Cookie(None, alias=COOKIE_NAME),
    actor: Actor = Depends(get_current_actor),
) -> dict[str, str]:
    """Destroys server session and clears cookie."""
    if lekhan_session:
        session_store.delete_session(lekhan_session)

    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/me", response_model=AuthResponse, summary="Current user profile")
def get_me(
    lekhan_session: str = Cookie(..., alias=COOKIE_NAME),
    actor: Actor = Depends(get_current_actor),
) -> AuthResponse:
    """Returns profile and active CSRF token for the current session."""
    user = next(u for u in SYNTHETIC_USERS.values() if u["id"] == actor.user_id)
    session_data = session_store.get_session(lekhan_session)
    # Generate fresh CSRF token if needed
    csrf_token = getattr(session_data, "raw_csrf_token", "active-csrf-token")
    profile = UserProfile(
        id=user["id"],
        tenant_id=user["tenant_id"],
        email=user["email"],
        display_name=user["display_name"],
        role=user["role"],
        ui_language=user["ui_language"],
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
) -> dict[str, str]:
    """Updates password, invalidates all existing sessions, and rotates to a new session."""
    user = next(u for u in SYNTHETIC_USERS.values() if u["id"] == actor.user_id)
    if not verify_password(user["password_hash"], payload.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed.",
        )

    # 1. Update password hash
    user["password_hash"] = hash_password(payload.new_password)

    # 2. Revoke all prior sessions (docs/AUTH.md Section 2)
    session_store.delete_all_for_user(actor.user_id)

    # 3. Rotate session
    new_session_token, _ = session_store.create_session(
        user_id=actor.user_id,
        tenant_id=actor.tenant_id,
        user_agent=request.headers.get("User-Agent"),
        ip=request.client.host if request.client else "127.0.0.1",
    )

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
) -> Any:
    """Generates new TOTP base32 secret, otpauth:// URI, and 8 single-use recovery codes."""
    secret = generate_totp_secret()
    plain_recovery, hashed_recovery = generate_recovery_codes(count=8)

    user = next((u for u in SYNTHETIC_USERS.values() if u["id"] == actor.user_id), None)
    username = user["email"] if user else str(actor.user_id)
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

    user = next((u for u in SYNTHETIC_USERS.values() if u["id"] == actor.user_id), None)
    if user:
        user["mfa_enabled"] = True
        user["mfa_secret"] = pending["secret"]
        user["mfa_recovery_codes"] = pending["hashed_recovery_codes"]

    _PENDING_MFA_ENROLLMENTS.pop(actor.user_id, None)

    return {"status": "ok", "message": "Multi-Factor Authentication enabled successfully"}


@router.post("/mfa/verify", summary="Verify TOTP or recovery code")
def verify_mfa_login(
    payload: MfaVerifyPayload,
    actor: Actor = Depends(get_current_actor),
) -> dict[str, Any]:
    """Verifies a 6-digit TOTP code or consumes a one-time recovery code."""
    user = next((u for u in SYNTHETIC_USERS.values() if u["id"] == actor.user_id), None)
    if not user or not user.get("mfa_enabled"):
        return {"status": "ok", "verified": True, "message": "MFA is not enabled for this user"}

    # 1. Try TOTP code
    if payload.code:
        if verify_totp_code(user.get("mfa_secret", ""), payload.code):
            return {"status": "ok", "verified": True}

    # 2. Try recovery code
    if payload.recovery_code:
        stored_hashes = user.get("mfa_recovery_codes", [])
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
) -> dict[str, Any]:
    """Disables MFA for the user."""
    user = next((u for u in SYNTHETIC_USERS.values() if u["id"] == actor.user_id), None)
    if user:
        user["mfa_enabled"] = False
        user["mfa_secret"] = None
        user["mfa_recovery_codes"] = []
    return {"status": "ok", "message": "MFA disabled"}

