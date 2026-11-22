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
import hmac
import time
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
from app.identity.throttling import InMemoryThrottler, login_throttler
from app.shared.crypto import decrypt_mfa_secret, encrypt_mfa_secret
from app.shared.logging import get_logger
from app.shared.models import MfaPendingEnrollment
from app.shared.network import get_client_ip
from app.shared.security import (
    derive_csrf_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_csrf_token,
    verify_password,
)

logger = get_logger(__name__)
settings = get_settings()

# Constant-time dummy hash to defeat timing enumeration of usernames
DUMMY_PASSWORD_HASH = hash_password("dummy_password_for_constant_time_enumeration_protection")

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
    mfa_required: bool = False


# --- Repository Dependencies ---


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    """Provides the UserRepository scoped to the current database session."""
    return PostgresUserRepository(db)


def get_session_repo(db: Session = Depends(get_db)) -> SessionRepository:
    """Provides the SessionRepository scoped to the current database session."""
    return PostgresSessionRepository(db)


# --- Dependencies ---


def get_current_actor(
    request: Request,
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

    # Restrict mfa_pending session to ONLY /auth/mfa/verify (and /logout)
    if getattr(session_data, "mfa_pending", False):
        allowed_paths = {
            "/api/v1/auth/mfa/verify",
            "/auth/mfa/verify",
            "/api/v1/auth/logout",
            "/auth/logout",
        }
        normalized_path = request.url.path.rstrip("/")
        if normalized_path not in allowed_paths:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA verification required. Access restricted until MFA verification completes.",
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
) -> None:
    """Enforces constant-time CSRF token validation on state-changing operations."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    if not lekhan_session or not x_csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid.",
        )

    expected_csrf = derive_csrf_token(settings.SECRET_KEY, lekhan_session)
    if not hmac.compare_digest(expected_csrf, x_csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token verification failed.",
        )


auth_csrf_router = APIRouter(dependencies=[Depends(require_csrf)])


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
    client_ip = get_client_ip(request)
    account_key = f"account:{payload.email.lower().strip()}"
    ip_key = f"ip:{client_ip}"

    # 1. Check rate-limit & lockout per-account AND per-IP
    acct_locked, acct_rem = login_throttler.is_locked(account_key)
    ip_locked, ip_rem = login_throttler.is_locked(ip_key)

    if acct_locked or ip_locked:
        remaining_seconds = max(acct_rem, ip_rem)
        logger.warning(
            "Throttled login attempt for %s from IP %s (acct_locked=%s, ip_locked=%s)",
            payload.email,
            client_ip,
            acct_locked,
            ip_locked,
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED
            if remaining_seconds > 60
            else status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account or IP temporarily locked due to repeated failures. Retry in {remaining_seconds}s.",
            headers={"Retry-After": str(remaining_seconds)},
        )

    # 2. Lookup user and verify password (always run dummy hash on missing user for constant-time)
    user = user_repo.find_by_email(tenant_id=None, email=payload.email)
    if not user:
        # Prevent timing-based user enumeration
        verify_password(DUMMY_PASSWORD_HASH, payload.password)
        login_throttler.record_failure(account_key)
        login_throttler.record_failure(ip_key)
        logger.info("Failed login attempt for nonexistent user %s from %s", payload.email, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(user.password_hash, payload.password):
        login_throttler.record_failure(account_key)
        login_throttler.record_failure(ip_key)
        user_repo.record_failed_login(tenant_id=user.tenant_id, user_id=user.id)
        logger.info("Failed login attempt (bad password) for %s from %s", payload.email, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account inactive.",
        )

    # 3. Successful authentication: reset throttlers for account AND IP
    login_throttler.record_success(account_key)
    login_throttler.record_success(ip_key)
    user_repo.reset_failed_logins(tenant_id=user.tenant_id, user_id=user.id)

    # 4. Check MFA requirements & enrollment
    is_mfa_enrolled = bool(user.mfa_secret_enc)
    is_mfa_enforced = settings.ENFORCE_MFA and user.role in (
        "admin",
        "reviewer",
        "template_admin",
    )

    if is_mfa_enforced and not is_mfa_enrolled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"MFA enrollment is mandatory for role '{user.role}'. Please complete MFA setup.",
        )

    # 5. Create fresh session token (Session Rotation)
    user_agent = request.headers.get("User-Agent")
    session_token = generate_opaque_token(32)
    csrf_token = derive_csrf_token(settings.SECRET_KEY, session_token)

    id_hash = hash_token(session_token)
    csrf_hash = hash_token(csrf_token)

    now = datetime.datetime.now(datetime.timezone.utc)

    profile = UserProfile(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        ui_language=user.ui_language,
    )

    if is_mfa_enrolled:
        # Issue short-lived mfa_pending session (5-minute TTL authorizing ONLY /auth/mfa/verify)
        mfa_expires_at = now + datetime.timedelta(minutes=5)
        mfa_session = SessionData(
            id_hash=id_hash,
            user_id=user.id,
            tenant_id=user.tenant_id,
            csrf_token_hash=csrf_hash,
            created_at=now,
            last_seen_at=now,
            expires_at=mfa_expires_at,
            user_agent=user_agent,
            ip=client_ip,
            mfa_pending=True,
        )
        session_repo.save(tenant_id=user.tenant_id, session=mfa_session)
        response.set_cookie(
            key=COOKIE_NAME,
            value=session_token,
            httponly=True,
            samesite="lax",
            secure=(not settings.is_dev),
            path="/",
        )
        response.headers["X-MFA-Required"] = "true"
        return AuthResponse(user=profile, csrf_token=csrf_token, mfa_required=True)

    # Full session (MFA not enrolled)
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
        mfa_pending=False,
    )
    session_repo.save(tenant_id=user.tenant_id, session=session_data)

    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=(not settings.is_dev),
        path="/",
    )

    return AuthResponse(user=profile, csrf_token=csrf_token, mfa_required=False)


@auth_csrf_router.post("/logout", summary="User logout")
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
) -> AuthResponse:
    """Returns profile and active CSRF token derived from the current session."""
    user = user_repo.get_by_id(tenant_id=actor.tenant_id, user_id=actor.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    csrf_token = derive_csrf_token(settings.SECRET_KEY, lekhan_session)
    profile = UserProfile(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        ui_language=user.ui_language,
    )
    return AuthResponse(user=profile, csrf_token=csrf_token)


@auth_csrf_router.post("/password/change", summary="Change password")
def change_password(
    payload: PasswordChangePayload,
    response: Response,
    request: Request,
    lekhan_session: str = Cookie(..., alias=COOKIE_NAME),
    actor: Actor = Depends(get_current_actor),
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
    new_csrf_token = derive_csrf_token(settings.SECRET_KEY, new_session_token)
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
        ip=get_client_ip(request),
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
    password: str


class MfaDisablePayload(BaseModel):
    code: str
    password: str


class MfaVerifyPayload(BaseModel):
    code: str | None = None
    recovery_code: str | None = None


# Throttler for /mfa/verify
mfa_throttler = InMemoryThrottler()

# In-memory replay cache: (user_id, code) -> timestamp (validity window)
_USED_TOTP_CODES: dict[str, float] = {}


def is_totp_replayed(user_id: uuid.UUID, code: str) -> bool:
    """Checks if a TOTP code was already consumed within the validity window."""
    now = time.time()
    # Expire old entries (> 90 seconds)
    expired = [k for k, t in _USED_TOTP_CODES.items() if now - t > 90]
    for k in expired:
        _USED_TOTP_CODES.pop(k, None)

    key = f"{user_id}:{code.strip()}"
    return key in _USED_TOTP_CODES


def record_used_totp(user_id: uuid.UUID, code: str) -> None:
    """Marks a TOTP code as consumed to prevent replay attacks."""
    _USED_TOTP_CODES[f"{user_id}:{code.strip()}"] = time.time()


@auth_csrf_router.post("/mfa/setup", response_model=MfaSetupResponse, summary="Initiate TOTP MFA setup")
def setup_mfa(
    actor: Actor = Depends(get_current_actor),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
) -> Any:
    """Generates new TOTP base32 secret, otpauth:// URI, and 8 single-use recovery codes, stored with 10-min TTL in DB."""
    now = datetime.datetime.now(datetime.timezone.utc)

    # Clean up expired pending enrollments
    db.query(MfaPendingEnrollment).filter(MfaPendingEnrollment.expires_at < now).delete()

    secret = generate_totp_secret()
    plain_recovery, hashed_recovery = generate_recovery_codes(count=8)

    user = user_repo.get_by_id(tenant_id=actor.tenant_id, user_id=actor.user_id)
    username = user.email if user else str(actor.user_id)
    otpauth_uri = build_otpauth_uri(secret=secret, username=username, issuer="Lekhan")

    secret_enc = encrypt_mfa_secret(secret)
    expires_at = now + datetime.timedelta(minutes=10)

    # Persist in DB with 10-minute TTL
    existing = (
        db.query(MfaPendingEnrollment)
        .filter(MfaPendingEnrollment.user_id == actor.user_id)
        .first()
    )
    if existing:
        existing.secret_enc = secret_enc
        existing.hashed_recovery_codes = hashed_recovery
        existing.expires_at = expires_at
    else:
        pending = MfaPendingEnrollment(
            user_id=actor.user_id,
            secret_enc=secret_enc,
            hashed_recovery_codes=hashed_recovery,
            expires_at=expires_at,
        )
        db.add(pending)
    db.commit()

    return MfaSetupResponse(
        secret=secret,
        otpauth_uri=otpauth_uri,
        recovery_codes=plain_recovery,
    )


@auth_csrf_router.post("/mfa/enable", summary="Verify TOTP code and activate MFA")
def enable_mfa(
    payload: MfaEnablePayload,
    actor: Actor = Depends(get_current_actor),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Verifies password and 6-digit TOTP code against DB-stored pending secret and activates MFA."""
    user = user_repo.get_by_id(tenant_id=actor.tenant_id, user_id=actor.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # 1. Require current password
    if not verify_password(user.password_hash, payload.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed.",
        )

    # 2. Retrieve pending enrollment from DB with 10-minute TTL
    now = datetime.datetime.now(datetime.timezone.utc)
    pending = (
        db.query(MfaPendingEnrollment)
        .filter(
            MfaPendingEnrollment.user_id == actor.user_id,
            MfaPendingEnrollment.expires_at >= now,
        )
        .first()
    )
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending MFA setup found or session expired (10-minute TTL). Call /mfa/setup first.",
        )

    # 3. Decrypt secret and verify code
    secret = decrypt_mfa_secret(pending.secret_enc)
    if not verify_totp_code(secret, payload.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 6-digit verification code. Please check your authenticator clock.",
        )

    # 4. Activate MFA on user
    user.mfa_secret_enc = pending.secret_enc
    user.mfa_recovery_codes = pending.hashed_recovery_codes
    user_repo.update(tenant_id=actor.tenant_id, user=user)

    # 5. Consume pending enrollment
    db.delete(pending)
    db.commit()

    return {"status": "ok", "message": "Multi-Factor Authentication enabled successfully"}


@auth_csrf_router.post("/mfa/verify", summary="Verify TOTP or recovery code")
def verify_mfa_login(
    payload: MfaVerifyPayload,
    request: Request,
    response: Response,
    lekhan_session: str = Cookie(..., alias=COOKIE_NAME),
    actor: Actor = Depends(get_current_actor),
    user_repo: UserRepository = Depends(get_user_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Verifies a 6-digit TOTP code or consumes a one-time recovery code, promoting session."""
    client_ip = get_client_ip(request)
    throttle_key = f"mfa:{actor.user_id}:{client_ip}"

    # Rate limiting on /mfa/verify
    is_locked, remaining = mfa_throttler.is_locked(throttle_key)
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed MFA verification attempts. Retry in {remaining}s.",
            headers={"Retry-After": str(remaining)},
        )

    user = user_repo.get_by_id(tenant_id=actor.tenant_id, user_id=actor.user_id)
    if not user or not user.mfa_secret_enc:
        return {"status": "ok", "verified": True, "message": "MFA is not enabled for this user"}

    verified = False
    recovery_used = False

    # 1. Try TOTP code
    if payload.code:
        if is_totp_replayed(actor.user_id, payload.code):
            mfa_throttler.record_failure(throttle_key)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="TOTP code has already been used. Please wait for the next code.",
            )

        secret = decrypt_mfa_secret(user.mfa_secret_enc)
        if verify_totp_code(secret, payload.code):
            verified = True
            record_used_totp(actor.user_id, payload.code)

    # 2. Try recovery code
    elif payload.recovery_code:
        stored_hashes = list(getattr(user, "mfa_recovery_codes", []) or [])
        if verify_and_consume_recovery_code(payload.recovery_code, stored_hashes):
            verified = True
            recovery_used = True
            # Atomically persist consumed recovery code
            user.mfa_recovery_codes = stored_hashes
            user_repo.update(tenant_id=actor.tenant_id, user=user)

    if not verified:
        mfa_throttler.record_failure(throttle_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA code or recovery code.",
        )

    mfa_throttler.record_success(throttle_key)

    # Promote session: delete mfa_pending session and issue full session (Session Rotation)
    old_id_hash = hash_token(lekhan_session)
    session_repo.delete(tenant_id=actor.tenant_id, id_hash=old_id_hash)

    new_session_token = generate_opaque_token(32)
    new_csrf_token = derive_csrf_token(settings.SECRET_KEY, new_session_token)
    new_id_hash = hash_token(new_session_token)
    new_csrf_hash = hash_token(new_csrf_token)
    now = datetime.datetime.now(datetime.timezone.utc)
    new_expires_at = now + datetime.timedelta(hours=ABSOLUTE_TIMEOUT_HOURS)

    full_session = SessionData(
        id_hash=new_id_hash,
        user_id=actor.user_id,
        tenant_id=actor.tenant_id,
        csrf_token_hash=new_csrf_hash,
        created_at=now,
        last_seen_at=now,
        expires_at=new_expires_at,
        user_agent=request.headers.get("User-Agent"),
        ip=client_ip,
        mfa_pending=False,
    )
    session_repo.save(tenant_id=actor.tenant_id, session=full_session)

    response.set_cookie(
        key=COOKIE_NAME,
        value=new_session_token,
        httponly=True,
        samesite="lax",
        secure=(not settings.is_dev),
        path="/",
    )

    return {
        "status": "ok",
        "verified": True,
        "csrf_token": new_csrf_token,
        "recovery_code_used": recovery_used,
    }


@auth_csrf_router.post("/mfa/disable", summary="Disable MFA")
def disable_mfa(
    payload: MfaDisablePayload,
    actor: Actor = Depends(get_current_actor),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Disables MFA for the user, requiring current password and valid TOTP code."""
    user = user_repo.get_by_id(tenant_id=actor.tenant_id, user_id=actor.user_id)
    if not user or not user.mfa_secret_enc:
        return {"status": "ok", "message": "MFA is not enabled for this user"}

    # 1. Require current password
    if not verify_password(user.password_hash, payload.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed.",
        )

    # 2. Require valid TOTP code
    secret = decrypt_mfa_secret(user.mfa_secret_enc)
    valid_code = verify_totp_code(secret, payload.code)
    if not valid_code:
        stored_hashes = list(getattr(user, "mfa_recovery_codes", []) or [])
        valid_code = verify_and_consume_recovery_code(payload.code, stored_hashes)

    if not valid_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA verification code.",
        )

    user.mfa_secret_enc = None
    user.mfa_recovery_codes = []
    user_repo.update(tenant_id=actor.tenant_id, user=user)

    # Clean any pending enrollment
    db.query(MfaPendingEnrollment).filter(MfaPendingEnrollment.user_id == actor.user_id).delete()
    db.commit()

    return {"status": "ok", "message": "MFA disabled"}


# Include CSRF-protected auth sub-routes into main auth router
router.include_router(auth_csrf_router)
