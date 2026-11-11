"""Security and cryptographic helpers for authentication and sessions.

Implements:
- Argon2id password hashing with fallback to PBKDF2-SHA256
- Constant-time digest comparisons
- SHA-256 session and CSRF token hashing
- Cryptographically secure token generation
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

try:
    from argon2 import PasswordHasher  # type: ignore[import-not-found]
    from argon2.exceptions import VerifyMismatchError  # type: ignore[import-not-found]

    _hasher: PasswordHasher | None = PasswordHasher(
        time_cost=2,
        memory_cost=65536,
        parallelism=2,
        hash_len=32,
        salt_len=16,
    )
except ImportError:
    _hasher = None


def hash_password(password: str) -> str:
    """Hashes a password with argon2id (or PBKDF2-HMAC-SHA256 if argon2 is unavailable)."""
    if _hasher is not None:
        return str(_hasher.hash(password))
    # Fallback when argon2 C-extensions are not yet compiled
    salt = secrets.token_bytes(16)
    kdf = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"pbkdf2:sha256:100000${salt.hex()}${kdf.hex()}"


def verify_password(hash_str: str, password: str) -> bool:
    """Verifies a plain password against an argon2id or PBKDF2 hash in constant time."""
    if hash_str.startswith("$argon2"):
        if _hasher is None:
            return False
        try:
            return bool(_hasher.verify(hash_str, password))
        except VerifyMismatchError:
            return False
        except Exception:
            return False

    if hash_str.startswith("pbkdf2:sha256:"):
        try:
            parts = hash_str.split("$")
            if len(parts) == 3:
                prefix, salt_hex, hash_hex = parts
                iterations = int(prefix.split(":")[2])
            elif len(parts) == 5:
                _, _, iterations_str, salt_hex, hash_hex = parts
                iterations = int(iterations_str)
            else:
                return False
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(hash_hex)
            computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(computed, expected)
        except Exception:
            return False

    return False


def generate_opaque_token(nbytes: int = 32) -> str:
    """Generates an opaque, cryptographically random base64url token."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> bytes:
    """Computes SHA-256 digest of a session or CSRF token for safe database storage."""
    return hashlib.sha256(token.encode("utf-8")).digest()


def verify_csrf_token(stored_hash: bytes, supplied_token: str) -> bool:
    """Compares supplied CSRF token against stored SHA-256 hash in constant time."""
    supplied_hash = hash_token(supplied_token)
    return hmac.compare_digest(stored_hash, supplied_hash)
