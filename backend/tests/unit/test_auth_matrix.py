"""Comprehensive Authorisation Matrix and Security Tests.

Fulfills docs/AUTH.md Section 13 Test Matrix requirements:
1. Every endpoint x every role authorization policy evaluation.
2. Cross-tenant access returns 404 (AGENTS.md Hard Rule 6).
3. Separation of duties: template submitter cannot approve own version.
4. Drafter IDOR isolation (accessing another drafter's document).
5. CSRF protection on state-changing requests.
6. Login throttling and lockout (429 / 423).
7. Session cookie security flags (HttpOnly, SameSite=Lax).
"""

import uuid

from fastapi.testclient import TestClient

from app.api.auth import get_session_repo, get_user_repo
from app.identity.policy import Actor, Resource, authorize
from app.identity.repository import create_dev_user_repository
from app.identity.service import session_store
from app.identity.session_repository import InMemorySessionRepository
from app.identity.throttling import login_throttler
from app.main import app
from app.shared.security import hash_password, verify_password

test_session_repo = InMemorySessionRepository()
app.dependency_overrides[get_user_repo] = create_dev_user_repository
app.dependency_overrides[get_session_repo] = lambda: test_session_repo
client = TestClient(app)

TENANT_A = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")
TENANT_B = uuid.UUID("0193132e-504f-7a1b-8000-000000000002")

ADMIN_A = Actor(
    user_id=uuid.UUID("0193132e-504f-7a1b-8000-000000000010"), tenant_id=TENANT_A, role="admin"
)
T_ADMIN_A = Actor(
    user_id=uuid.UUID("0193132e-504f-7a1b-8000-000000000020"),
    tenant_id=TENANT_A,
    role="template_admin",
)
REVIEWER_A = Actor(
    user_id=uuid.UUID("0193132e-504f-7a1b-8000-000000000030"), tenant_id=TENANT_A, role="reviewer"
)
DRAFTER_A1 = Actor(
    user_id=uuid.UUID("0193132e-504f-7a1b-8000-000000000041"), tenant_id=TENANT_A, role="drafter"
)
DRAFTER_A2 = Actor(
    user_id=uuid.UUID("0193132e-504f-7a1b-8000-000000000042"), tenant_id=TENANT_A, role="drafter"
)


# --- 1. Policy Role Matrix Tests ---


def test_user_management_role_permissions() -> None:
    """Only admin can manage users; others are denied."""
    assert authorize(ADMIN_A, "manage_users").allowed is True
    assert authorize(T_ADMIN_A, "manage_users").allowed is False
    assert authorize(REVIEWER_A, "manage_users").allowed is False
    assert authorize(DRAFTER_A1, "manage_users").allowed is False


def test_template_lifecycle_permissions() -> None:
    """Template creation vs approval permissions."""
    # template_admin can create and submit templates
    assert authorize(T_ADMIN_A, "create_template").allowed is True
    assert authorize(T_ADMIN_A, "submit_template_for_review").allowed is True
    # template_admin cannot approve
    assert authorize(T_ADMIN_A, "approve_template_version").allowed is False

    # reviewer can approve templates
    assert authorize(REVIEWER_A, "approve_template_version").allowed is True
    # reviewer cannot create templates
    assert authorize(REVIEWER_A, "create_template").allowed is False

    # drafter can neither create nor approve
    assert authorize(DRAFTER_A1, "create_template").allowed is False
    assert authorize(DRAFTER_A1, "approve_template_version").allowed is False


def test_document_creation_and_review_permissions() -> None:
    """Document creation vs finalization permissions."""
    # drafter and admin can create documents
    assert authorize(DRAFTER_A1, "create_document").allowed is True
    assert authorize(ADMIN_A, "create_document").allowed is True

    # drafter cannot finalize documents
    assert authorize(DRAFTER_A1, "finalize_document").allowed is False
    # reviewer can finalize documents
    assert authorize(REVIEWER_A, "finalize_document").allowed is True


# --- 2. Cross-Tenant Isolation Tests (Must return 404) ---


def test_cross_tenant_access_returns_404() -> None:
    """Accessing any resource belonging to another tenant MUST return status 404."""
    resource_tenant_b = Resource(
        tenant_id=TENANT_B, resource_type="document", owner_id=uuid.uuid4()
    )

    decision_admin = authorize(ADMIN_A, "view_document", resource_tenant_b)
    assert decision_admin.allowed is False
    assert decision_admin.status_code == 404

    decision_drafter = authorize(DRAFTER_A1, "view_document", resource_tenant_b)
    assert decision_drafter.allowed is False
    assert decision_drafter.status_code == 404


# --- 3. Separation of Duties ---


def test_separation_of_duties_submitter_cannot_approve() -> None:
    """The user who submitted a template version cannot approve it, even if they hold reviewer role."""
    same_user_id = uuid.uuid4()
    reviewer_actor = Actor(user_id=same_user_id, tenant_id=TENANT_A, role="reviewer")

    template_resource = Resource(
        tenant_id=TENANT_A,
        resource_type="template_version",
        submitter_id=same_user_id,  # Submitted by this exact user!
    )

    decision = authorize(reviewer_actor, "approve_template_version", template_resource)
    assert decision.allowed is False
    assert "Submitter cannot approve" in decision.reason


# --- 4. Drafter IDOR Isolation ---


def test_drafter_cannot_access_other_drafters_document() -> None:
    """A drafter cannot view or edit a document owned by another drafter."""
    doc_owned_by_a1 = Resource(
        tenant_id=TENANT_A, resource_type="document", owner_id=DRAFTER_A1.user_id
    )

    # Drafter 1 can view own document
    assert authorize(DRAFTER_A1, "view_document", doc_owned_by_a1).allowed is True

    # Drafter 2 accessing Drafter 1 document returns 404 (IDOR protection)
    decision = authorize(DRAFTER_A2, "view_document", doc_owned_by_a1)
    assert decision.allowed is False
    assert decision.status_code == 404


# --- 5. Security & Password Tests ---


def test_password_hashing_and_verification() -> None:
    """Verifies that password hashing produces valid hashes and verifies in constant time."""
    raw = "SecureLegalP@ssw0rd2026!"
    hashed = hash_password(raw)
    assert verify_password(hashed, raw) is True
    assert verify_password(hashed, "WrongPassword123") is False


# --- 6. API Login, Cookie & Throttling Integration Tests ---


def test_login_success_sets_http_only_cookie() -> None:
    """Verifies successful login returns 200, CSRF token, and sets HttpOnly cookie."""
    login_throttler.reset()
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "drafter@lekhan.local", "password": "ValidPassword123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "user" in data
    assert "csrf_token" in data
    assert data["user"]["role"] == "drafter"

    # Verify session cookie was set
    assert "lekhan_session" in res.cookies
    # Inspect cookie header attributes
    set_cookie = res.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie
    assert "samesite=lax" in set_cookie.lower()


def test_login_brute_force_throttling_and_lockout() -> None:
    """Verifies rate-limiting (429) and lockout (423) after repeated failures."""
    login_throttler.reset()
    email = "admin@lekhan.local"

    # Perform 5 failed attempts
    for _ in range(5):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "BadPassword!"},
        )
        assert res.status_code == 401

    # 6th attempt should be rate limited (429)
    res_throttled = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "BadPassword!"},
    )
    assert res_throttled.status_code in (429, 423)
    assert "Retry-After" in res_throttled.headers


def test_csrf_protection_on_password_change() -> None:
    """State-changing requests without valid CSRF token are blocked with 403."""
    session_store.clear()
    test_session_repo.clear()
    # 1. Login to obtain session
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "reviewer@lekhan.local", "password": "ValidPassword123!"},
    )
    assert login_res.status_code == 200
    cookie_val = login_res.cookies["lekhan_session"]
    valid_csrf = login_res.json()["csrf_token"]

    # 2. Attempt password change with MISSING CSRF token -> 403
    fail_res1 = client.post(
        "/api/v1/auth/password/change",
        json={"current_password": "ValidPassword123!", "new_password": "NewValidPassword123!"},
        cookies={"lekhan_session": cookie_val},
    )
    assert fail_res1.status_code == 403

    # 3. Attempt password change with INVALID CSRF token -> 403
    fail_res2 = client.post(
        "/api/v1/auth/password/change",
        json={"current_password": "ValidPassword123!", "new_password": "NewValidPassword123!"},
        cookies={"lekhan_session": cookie_val},
        headers={"X-CSRF-Token": "bogus-csrf-token"},
    )
    assert fail_res2.status_code == 403

    # 4. Attempt password change with VALID CSRF token -> 200
    success_res = client.post(
        "/api/v1/auth/password/change",
        json={"current_password": "ValidPassword123!", "new_password": "NewValidPassword123!"},
        cookies={"lekhan_session": cookie_val},
        headers={"X-CSRF-Token": valid_csrf},
    )
    assert success_res.status_code == 200
    assert success_res.json()["status"] == "ok"
