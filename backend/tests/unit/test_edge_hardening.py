"""Comprehensive unit tests for Edge Hardening.

Verifies:
1. TRUSTED_PROXIES config: only honors X-Forwarded-For from trusted peers, otherwise socket IP.
2. Metrics endpoint allowlist: removes "testclient" in staging/production (is_dev=False).
3. Body size limit enforcement on streamed and chunked request bodies (413 PAYLOAD_TOO_LARGE).
4. X-Correlation-ID validation: valid UUIDs preserved; malformed strings regenerated.
5. Login timing protection: dummy hash executed when user does not exist.
6. Login dual throttling: per-account AND per-IP rate limiting and lockout.
7. Throttler fails closed on database errors in staging/production (not falling back to memory).
8. Error hygiene: no internal str(exc) leaked on PDF and document generation errors.
9. Security headers: CSP (frame-ancestors 'none'), HSTS, nosniff, X-Frame-Options DENY.
"""

from __future__ import annotations

import uuid
from typing import Any, AsyncGenerator, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request, status
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.adapters.repositories.sessions import PostgresSessionRepository
from app.adapters.repositories.users import PostgresUserRepository
from app.api.auth import DUMMY_PASSWORD_HASH, get_session_repo, get_user_repo, login_throttler
from app.config import get_settings
from app.identity.models import UserRecord
from app.identity.policy import Actor
from app.identity.throttling import DatabaseThrottler, InMemoryThrottler
from app.main import app
from app.shared.errors import AppError
from app.shared.network import get_client_ip
from app.shared.security import hash_password

settings = get_settings()

TENANT_ID = uuid.UUID("0193132e-504f-7a1b-8000-000000000001")


# --- 1. TRUSTED_PROXIES and X-Forwarded-For Tests ---


def test_trusted_proxies_x_forwarded_for() -> None:
    """Verifies X-Forwarded-For is only trusted from allowed proxy socket IPs."""
    trusted_proxies = ["10.0.0.1", "127.0.0.1"]

    # Case A: Request from untrusted socket IP (203.0.113.50) spoofing X-Forwarded-For
    req_untrusted = MagicMock(spec=Request)
    req_untrusted.client = MagicMock()
    req_untrusted.client.host = "203.0.113.50"
    req_untrusted.headers = {"X-Forwarded-For": "198.51.100.1"}

    resolved_ip = get_client_ip(req_untrusted, trusted_proxies=trusted_proxies)
    assert resolved_ip == "203.0.113.50", "Must ignore X-Forwarded-For from untrusted peer"

    # Case B: Request from trusted proxy (10.0.0.1) forwarding genuine client IP
    req_trusted = MagicMock(spec=Request)
    req_trusted.client = MagicMock()
    req_trusted.client.host = "10.0.0.1"
    req_trusted.headers = {"X-Forwarded-For": "198.51.100.1, 10.0.0.1"}

    resolved_trusted = get_client_ip(req_trusted, trusted_proxies=trusted_proxies)
    assert resolved_trusted == "198.51.100.1", "Must honor client IP from trusted reverse proxy"

    # Case C: Request from trusted proxy with missing/empty header
    req_empty_header = MagicMock(spec=Request)
    req_empty_header.client = MagicMock()
    req_empty_header.client.host = "10.0.0.1"
    req_empty_header.headers = {}

    assert get_client_ip(req_empty_header, trusted_proxies=trusted_proxies) == "10.0.0.1"


# --- 2. Production Metrics Allowlist Excludes "testclient" ---


def test_metrics_testclient_in_production() -> None:
    """Verifies 'testclient' is forbidden in production/staging environments."""
    client = TestClient(app, raise_server_exceptions=False)

    # 1. In dev environment, local testclient is allowed
    with patch.object(settings, "ENV", "dev"):
        res_dev = client.get("/metrics")
        assert res_dev.status_code == status.HTTP_200_OK

    # 2. In production environment, testclient is removed from the allowlist
    with patch.object(settings, "ENV", "prod"):
        res_prod = client.get("/metrics")
        assert res_prod.status_code == status.HTTP_403_FORBIDDEN
        assert "access is restricted" in res_prod.json()["detail"].lower()


# --- 3. Enforce Body Size on Streamed / Chunked Requests ---


def test_streamed_chunked_body_size_enforced() -> None:
    """Verifies that streamed or chunked request exceeding max_bytes returns 413."""
    client = TestClient(app, raise_server_exceptions=False)

    # Send a payload that exceeds the default limit with chunked transfer
    oversized_chunk = b"X" * (1024 * 1024)  # 1 MB chunk

    def chunk_generator() -> Generator[bytes, None, None]:
        # Yield 12 chunks (12 MB > 10 MB limit)
        for _ in range(12):
            yield oversized_chunk

    # Post streamed chunks to an endpoint
    res = client.post(
        "/api/v1/auth/login",
        content=chunk_generator(),
        headers={"Transfer-Encoding": "chunked"},
    )
    assert res.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    data = res.json()
    assert data["code"] == "PAYLOAD_TOO_LARGE"
    assert "exceeds maximum limit" in data["detail"]

    # Also verify immediate rejection on Content-Length header
    res_cl = client.post(
        "/api/v1/auth/login",
        content=b"test",
        headers={"Content-Length": str(15 * 1024 * 1024)},
    )
    assert res_cl.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    assert res_cl.json()["code"] == "PAYLOAD_TOO_LARGE"


# --- 4. Validate X-Correlation-ID (UUID Format Else Regenerate) ---


def test_correlation_id_validation_and_regeneration() -> None:
    """Verifies that valid UUIDs are kept, while malformed/injection strings are replaced with UUIDs."""
    client = TestClient(app, raise_server_exceptions=False)

    # 1. Valid UUIDv4/v7 should be preserved exactly
    valid_uuid = "0193132e-504f-7a1b-8000-000000000001"
    res1 = client.get("/health/live", headers={"X-Correlation-ID": valid_uuid})
    assert res1.status_code == status.HTTP_200_OK
    assert res1.headers.get("X-Correlation-ID") == valid_uuid

    # 2. Malformed / malicious string must be discarded and replaced with a valid UUID
    malformed_cid = "<script>alert(1)</script>; DROP TABLE users;--"
    res2 = client.get("/health/live", headers={"X-Correlation-ID": malformed_cid})
    assert res2.status_code == status.HTTP_200_OK
    returned_cid = res2.headers.get("X-Correlation-ID")
    assert returned_cid is not None
    assert returned_cid != malformed_cid
    # Must parse successfully as a UUID
    parsed = uuid.UUID(returned_cid)
    assert str(parsed) == returned_cid


# --- 5. Login Dummy Hash for Non-existent Users ---


def test_login_dummy_hash_timing_safety() -> None:
    """Verifies verify_password is executed with DUMMY_PASSWORD_HASH for non-existent users."""
    mock_user_repo = MagicMock()
    mock_user_repo.find_by_email.return_value = None  # User does not exist

    app.dependency_overrides[get_user_repo] = lambda: mock_user_repo
    client = TestClient(app, raise_server_exceptions=False)

    with patch("app.api.auth.verify_password", wraps=lambda h, p: False) as mock_verify:
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent_user@example.com", "password": "SamplePassword123!"},
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
        # Must have verified against DUMMY_PASSWORD_HASH to prevent timing attacks
        assert mock_verify.called
        assert mock_verify.call_args[0][0] == DUMMY_PASSWORD_HASH

    app.dependency_overrides.clear()


# --- 6. Login Dual Throttling (Per-Account AND Per-IP) ---


def test_login_dual_throttling() -> None:
    """Verifies that throttling locks out either by target account OR by client IP."""
    login_throttler.reset()
    client = TestClient(app, raise_server_exceptions=False)

    # 1. Lock out specific Account A from IP 1
    target_account = "victim@example.com"
    for _ in range(5):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": target_account, "password": "WrongPassword!"},
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    # 6th attempt on target_account must be throttled
    res_account_locked = client.post(
        "/api/v1/auth/login",
        json={"email": target_account, "password": "WrongPassword!"},
    )
    assert res_account_locked.status_code in (status.HTTP_429_TOO_MANY_REQUESTS, status.HTTP_423_LOCKED)

    # 2. Reset and test IP lockout across different usernames
    login_throttler.reset()
    for i in range(5):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": f"user_{i}@example.com", "password": "WrongPassword!"},
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    # 6th attempt from same IP with a brand new email must also be throttled
    res_ip_locked = client.post(
        "/api/v1/auth/login",
        json={"email": "brand_new_user@example.com", "password": "WrongPassword!"},
    )
    assert res_ip_locked.status_code in (status.HTTP_429_TOO_MANY_REQUESTS, status.HTTP_423_LOCKED)


# --- 7. Throttler Fails Closed in Staging/Production ---


def test_throttler_fails_closed_in_production() -> None:
    """Verifies DatabaseThrottler fails closed (returns locked) during DB failure in prod/staging."""
    mock_session_factory = MagicMock()
    mock_session = MagicMock()
    mock_session.query.side_effect = OperationalError("DB down", params=None, orig=Exception())
    mock_session_factory.return_value.__enter__.return_value = mock_session

    throttler = DatabaseThrottler(session_factory=mock_session_factory)

    # In dev mode: falls back to in-memory
    with patch.object(settings, "ENV", "dev"):
        is_locked, remaining = throttler.is_locked("test_key")
        assert is_locked is False

    # In prod mode: must fail closed to protect authentication endpoints from brute force
    with patch.object(settings, "ENV", "prod"):
        is_locked, remaining = throttler.is_locked("test_key")
        assert is_locked is True
        assert remaining > 0

        # record_failure also fails closed
        failed_locked, lock_dur = throttler.record_failure("test_key")
        assert failed_locked is True


# --- 8. Error Hygiene (No str(exc) Leaked in PDF and Generation) ---


def test_no_str_exc_leak_in_pdf_and_generation() -> None:
    """Verifies that PDF and generation errors return domain codes and correlation IDs without str(exc)."""
    from app.api.auth import get_current_actor
    from app.api.documents import get_pipeline

    test_actor = Actor(
        user_id=uuid.UUID("0193132e-504f-7a1b-8000-000000000010"),
        tenant_id=TENANT_ID,
        role="drafter",
    )
    app.dependency_overrides[get_current_actor] = lambda: test_actor

    mock_pipeline = MagicMock()
    # Simulate low-level exception containing internal system details
    mock_pipeline.get_document.return_value = MagicMock(
        tenant_id=TENANT_ID,
        doc_no="DOC/2026/001",
    )
    mock_pipeline.get_or_create_pdf.side_effect = RuntimeError(
        "Internal LibreOffice crashed at /var/lib/soffice.bin: signal 11 with secret_key_123"
    )
    app.dependency_overrides[get_pipeline] = lambda: mock_pipeline

    client = TestClient(app, raise_server_exceptions=False)

    doc_id = uuid.uuid4()
    res = client.get(f"/api/v1/documents/{doc_id}/pdf")
    assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    data = res.json()
    assert data["code"] == "PDF_GENERATION_FAILED"
    assert "correlation_id" in data
    assert data["correlation_id"] is not None
    # Verify internal details or exception string are NOT leaked to the client
    assert "soffice.bin" not in data["detail"]
    assert "secret_key_123" not in data["detail"]
    assert "signal 11" not in data["detail"]

    # 2. Test document generation failure sanitization
    from app.api.documents import get_job_repo
    from app.generation.jobs import InMemoryJobRepository
    from app.shared.security import derive_csrf_token
    from app.worker import run_worker_once

    repo = InMemoryJobRepository()
    repo.clear()
    mock_pipeline.process_job.side_effect = ValueError(
        "Corrupted docx tag syntax at byte 0x4F: secret_internal_var"
    )

    app.dependency_overrides[get_current_actor] = lambda: test_actor
    app.dependency_overrides[get_pipeline] = lambda: mock_pipeline
    app.dependency_overrides[get_job_repo] = lambda: repo

    csrf_token = derive_csrf_token(settings.SECRET_KEY, "edge-test-session")
    res_gen = client.post(
        "/api/v1/documents",
        json={"template_id": "plot_sale_deed", "data": {}},
        cookies={"lekhan_session": "edge-test-session"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res_gen.status_code == status.HTTP_202_ACCEPTED
    job_id = res_gen.json()["job_id"]

    # Worker executes and handles failure with sanitized error
    with patch("app.worker.generation_pipeline", mock_pipeline):
        run_worker_once(repo=repo)

    # Poll /jobs/{id}
    res_poll = client.get(f"/jobs/{job_id}", cookies={"lekhan_session": "edge-test-session"})
    assert res_poll.status_code == 200
    gen_data = res_poll.json()
    assert gen_data["status"] == "failed"
    assert gen_data["error"]["code"] == "VALIDATION_FAILED"
    assert "correlation_id" in gen_data["error"]
    assert "secret_internal_var" not in gen_data["error"]["message"]

    app.dependency_overrides.clear()


# --- 9. Defense-in-Depth Security Headers ---


def test_security_headers_present() -> None:
    """Verifies presence and values of CSP, HSTS, X-Content-Type-Options, and frame-ancestors none."""
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/health/live")
    assert res.status_code == status.HTTP_200_OK

    headers = res.headers
    # Content-Security-Policy
    csp = headers.get("Content-Security-Policy", "")
    assert "frame-ancestors 'none'" in csp
    assert "default-src 'self'" in csp

    # Strict-Transport-Security
    hsts = headers.get("Strict-Transport-Security", "")
    assert "max-age=" in hsts
    assert "includeSubDomains" in hsts

    # X-Content-Type-Options
    assert headers.get("X-Content-Type-Options") == "nosniff"

    # X-Frame-Options
    assert headers.get("X-Frame-Options") == "DENY"

    # Referrer-Policy and Permissions-Policy
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in headers.get("Permissions-Policy", "")
