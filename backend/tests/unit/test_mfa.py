"""Unit tests for TOTP MFA and Recovery Codes (PRD FR-01, Features F-005, AUTH.md Section 6).

Verifies:
1. RFC 6238 TOTP code generation and time window verification.
2. Clock drift tolerance (+-1 step window).
3. Rejection of invalid codes and expired timestamps.
4. Single-use recovery codes generation, validation, and burning.
5. Standard otpauth:// URI formatting.
"""

import time
import pytest

from app.identity.mfa import (
    build_otpauth_uri,
    generate_recovery_codes,
    generate_totp_code,
    generate_totp_secret,
    verify_and_consume_recovery_code,
    verify_totp_code,
)


def test_totp_code_generation_and_verification() -> None:
    """Verifies that a code generated for a secret verifies successfully."""
    secret = generate_totp_secret()
    assert len(secret) >= 16

    code = generate_totp_code(secret)
    assert len(code) == 6
    assert code.isdigit()

    # Code should verify immediately
    assert verify_totp_code(secret, code, window=1) is True


def test_totp_clock_drift_window() -> None:
    """Verifies that codes generated within +-30s window verify, but outside window fail."""
    secret = generate_totp_secret()
    now = time.time()

    code_current = generate_totp_code(secret, timestamp=now)
    code_past = generate_totp_code(secret, timestamp=now - 30)  # -1 step
    code_future = generate_totp_code(secret, timestamp=now + 30)  # +1 step
    code_too_old = generate_totp_code(secret, timestamp=now - 90)  # -3 steps (outside window)

    # Within window=1 tolerance
    assert verify_totp_code(secret, code_current, window=1) is True
    assert verify_totp_code(secret, code_past, window=1) is True
    assert verify_totp_code(secret, code_future, window=1) is True

    # Outside window
    assert verify_totp_code(secret, code_too_old, window=1) is False


def test_totp_invalid_codes_rejected() -> None:
    """Verifies rejection of malformed or invalid codes."""
    secret = generate_totp_secret()
    assert verify_totp_code(secret, "000000") is False
    assert verify_totp_code(secret, "abc123") is False
    assert verify_totp_code(secret, "") is False
    assert verify_totp_code(secret, "12345") is False


def test_recovery_codes_single_use_burning() -> None:
    """Verifies that recovery codes work once and are burned on use."""
    plain_codes, hashed_codes = generate_recovery_codes(count=4)
    assert len(plain_codes) == 4
    assert len(hashed_codes) == 4

    first_code = plain_codes[0]

    # 1. First consumption succeeds and removes code from stored hashes
    valid = verify_and_consume_recovery_code(first_code, hashed_codes)
    assert valid is True
    assert len(hashed_codes) == 3

    # 2. Second consumption of the same code fails (burned)
    valid_second = verify_and_consume_recovery_code(first_code, hashed_codes)
    assert valid_second is False

    # 3. Invalid code fails
    assert verify_and_consume_recovery_code("FAKE-CODE", hashed_codes) is False


def test_build_otpauth_uri() -> None:
    """Verifies otpauth URI structure for QR code generators."""
    secret = "JBSWY3DPEHPK3PXP"
    uri = build_otpauth_uri(secret=secret, username="advocate@lekhan.local", issuer="Lekhan")
    assert uri.startswith("otpauth://totp/Lekhan:advocate%40lekhan.local")
    assert f"secret={secret}" in uri
    assert "period=30" in uri

