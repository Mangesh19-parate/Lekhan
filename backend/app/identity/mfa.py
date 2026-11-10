"""TOTP Multi-Factor Authentication (RFC 6238) and Recovery Codes Engine.

PRD FR-01, Features F-005, AUTH.md Section 6:
- Pure Python standard library implementation (no heavy external deps).
- Time-based one-time password (30s step, 6 digits, SHA-1 HMAC per RFC 6238).
- Clock drift tolerance (+-1 step, i.e. 30s window).
- Cryptographically secure single-use recovery codes (hashed before storage).
- otpauth:// URI generation for Google Authenticator / Authy.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from typing import Any


def generate_totp_secret() -> str:
    """Generates a cryptographically random 20-byte base32 secret."""
    raw_bytes = secrets.token_bytes(20)
    return base64.b32encode(raw_bytes).decode("ascii").rstrip("=")


def _normalize_b32_secret(secret: str) -> bytes:
    """Decodes a base32 secret with missing padding tolerance."""
    clean = secret.strip().replace(" ", "").upper()
    padding_needed = (8 - len(clean) % 8) % 8
    clean += "=" * padding_needed
    return base64.b32decode(clean, casefold=True)


def generate_totp_code(secret: str, timestamp: float | None = None) -> str:
    """Generates a standard 6-digit TOTP code for a given timestamp (default: now)."""
    t = timestamp if timestamp is not None else time.time()
    counter = int(t // 30)

    key = _normalize_b32_secret(secret)
    # Pack counter as big-endian 8-byte unsigned integer
    counter_bytes = struct.pack(">Q", counter)

    # Compute HMAC-SHA1
    mac = hmac.new(key, counter_bytes, hashlib.sha1).digest()

    # Dynamic truncation
    offset = mac[-1] & 0x0F
    code_int = struct.unpack(">I", mac[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{code_int % 1000000:06d}"


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """Verifies a 6-digit TOTP code with +-window clock drift tolerance."""
    if not code or len(code.strip()) != 6 or not code.strip().isdigit():
        return False

    clean_code = code.strip()
    now = time.time()
    current_counter = int(now // 30)

    for offset in range(-window, window + 1):
        target_time = (current_counter + offset) * 30
        generated = generate_totp_code(secret, timestamp=target_time)
        if hmac.compare_digest(generated, clean_code):
            return True

    return False


def generate_recovery_codes(count: int = 8) -> tuple[list[str], list[str]]:
    """Generates random single-use recovery codes and their SHA-256 storage hashes."""
    plain_codes: list[str] = []
    hashed_codes: list[str] = []

    for _ in range(count):
        # 8-character hex code, e.g. "a1b2-c3d4"
        raw = secrets.token_hex(4)
        formatted = f"{raw[:4]}-{raw[4:]}".upper()
        plain_codes.append(formatted)

        h = hashlib.sha256(formatted.encode("utf-8")).hexdigest()
        hashed_codes.append(h)

    return plain_codes, hashed_codes


def verify_and_consume_recovery_code(
    plain_code: str,
    stored_hashes: list[str],
) -> bool:
    """Verifies recovery code and burns it by removing it from stored_hashes if valid."""
    clean = plain_code.strip().upper()
    target_hash = hashlib.sha256(clean.encode("utf-8")).hexdigest()

    for idx, h in enumerate(stored_hashes):
        if hmac.compare_digest(h, target_hash):
            stored_hashes.pop(idx)
            return True

    return False


def build_otpauth_uri(
    secret: str,
    username: str,
    issuer: str = "Lekhan",
) -> str:
    """Generates standard otpauth:// URI for authenticator app configuration."""
    from urllib.parse import quote

    safe_issuer = quote(issuer)
    safe_user = quote(username)
    return (
        f"otpauth://totp/{safe_issuer}:{safe_user}"
        f"?secret={secret}&issuer={safe_issuer}&algorithm=SHA1&digits=6&period=30"
    )

