"""Unit tests for universal CSRF route coverage and HMAC-derived session binding.

Verifies:
1. Every POST/PUT/PATCH/DELETE route across the entire application has require_csrf,
   with /api/v1/auth/login being the sole permitted exception.
2. CSRF tokens are derived statelessly as HMAC-SHA256(SECRET_KEY, session_id).
3. /api/v1/auth/me returns the HMAC-derived token (hardcoded 'active-csrf-token' removed).
4. Missing or invalid X-CSRF-Token on state-changing operations returns 403 Forbidden.
5. Reload-then-mutate flow: session reload from /me provides valid in-memory CSRF token
   enabling successful state mutations.
"""

from __future__ import annotations

import hashlib
import hmac
import uuid

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.api.auth import get_current_actor, require_csrf
from app.config import get_settings
from app.identity.policy import Actor
from app.main import app
from app.shared.security import derive_csrf_token

settings = get_settings()
client = TestClient(app, raise_server_exceptions=False)

TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
DRAFTER_ACTOR = Actor(
    user_id=uuid.UUID("0193132e-504f-7a1b-8000-000000000002"),
    tenant_id=TENANT_ID,
    role="drafter",
)


def test_all_state_changing_routes_have_csrf_dependency() -> None:
    """Enumerates app.routes and fails if any state-changing route lacks require_csrf."""
    unprotected_routes: list[str] = []
    exempt_paths = {"/api/v1/auth/login"}

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        state_changing = route.methods.intersection({"POST", "PUT", "PATCH", "DELETE"})
        if not state_changing:
            continue

        if route.path in exempt_paths:
            continue

        # Check route.dependencies (router-level or route-level) and route.dependant.dependencies
        all_deps = list(route.dependencies)
        if hasattr(route, "dependant") and route.dependant:
            all_deps.extend(route.dependant.dependencies)

        has_csrf = any(
            getattr(dep, "dependency", None) == require_csrf
            or getattr(dep, "call", None) == require_csrf
            for dep in all_deps
        )

        if not has_csrf:
            methods_str = ",".join(sorted(state_changing))
            unprotected_routes.append(f"{methods_str} {route.path}")

    assert (
        not unprotected_routes
    ), f"State-changing routes missing require_csrf dependency: {unprotected_routes}"


def test_csrf_token_derived_from_session_hmac() -> None:
    """Verifies that derive_csrf_token generates standard HMAC-SHA256 digests."""
    secret = "test-secret-key-for-hmac-verification-minimum-32-bytes"
    session_id = "test-session-opaque-token-12345"

    expected = hmac.new(
        secret.encode("utf-8"), session_id.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    derived = derive_csrf_token(secret, session_id)

    assert derived == expected
    assert len(derived) == 64

    # Changing session_id yields distinct token
    other_derived = derive_csrf_token(secret, "different-session")
    assert other_derived != derived


def test_auth_me_returns_derived_csrf_token() -> None:
    """Verifies GET /api/v1/auth/me returns the HMAC-derived CSRF token dynamically."""
    session_token = "sess_me_test_opaque_token_98765"
    expected_csrf = derive_csrf_token(settings.SECRET_KEY, session_token)

    app.dependency_overrides[get_current_actor] = lambda: DRAFTER_ACTOR
    try:
        res = client.get(
            "/api/v1/auth/me",
            cookies={"lekhan_session": session_token},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["csrf_token"] == expected_csrf
        assert data["csrf_token"] != "active-csrf-token"
    finally:
        app.dependency_overrides.pop(get_current_actor, None)


def test_post_without_csrf_token_returns_403() -> None:
    """State-changing requests without X-CSRF-Token header are rejected with 403."""
    session_token = "sess_test_csrf_missing"
    app.dependency_overrides[get_current_actor] = lambda: DRAFTER_ACTOR

    try:
        # 1. Missing X-CSRF-Token header
        res_no_header = client.post(
            "/api/v1/parties",
            json={"name": "Test Party"},
            cookies={"lekhan_session": session_token},
        )
        assert res_no_header.status_code == 403
        assert "CSRF token missing or invalid" in res_no_header.json()["detail"]

        # 2. Missing cookie
        expected_csrf = derive_csrf_token(settings.SECRET_KEY, session_token)
        res_no_cookie = client.post(
            "/api/v1/parties",
            json={"name": "Test Party"},
            headers={"X-CSRF-Token": expected_csrf},
        )
        assert res_no_cookie.status_code == 403

        # 3. Invalid/tampered X-CSRF-Token
        res_bad_token = client.post(
            "/api/v1/parties",
            json={"name": "Test Party"},
            cookies={"lekhan_session": session_token},
            headers={"X-CSRF-Token": "tampered_csrf_token_value"},
        )
        assert res_bad_token.status_code == 403
        assert "verification failed" in res_bad_token.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_actor, None)


def test_reload_then_mutate_end_to_end_flow() -> None:
    """Tests the in-memory reload-then-mutate flow without localStorage dependency."""
    session_token = "sess_reload_mutate_flow_token"
    app.dependency_overrides[get_current_actor] = lambda: DRAFTER_ACTOR

    try:
        # Step 1: Simulate page reload -> frontend calls GET /api/v1/auth/me on mount
        me_res = client.get(
            "/api/v1/auth/me",
            cookies={"lekhan_session": session_token},
        )
        assert me_res.status_code == 200
        in_memory_csrf_token = me_res.json()["csrf_token"]
        assert in_memory_csrf_token

        # Step 2: Frontend performs mutation with the refetched in-memory token
        mutate_res = client.post(
            "/api/v1/parties/detect-duplicates",
            json={"name": "शाम सुंदर", "pan": "ABCDE1234F"},
            cookies={"lekhan_session": session_token},
            headers={"X-CSRF-Token": in_memory_csrf_token},
        )
        # Should pass CSRF gate cleanly (status 200 OK)
        assert mutate_res.status_code == 200
    finally:
        app.dependency_overrides.pop(get_current_actor, None)
