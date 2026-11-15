"""Cryptographic utilities for envelope and field encryption using AES-256-GCM.

Features:
- Authenticated AES-GCM encryption with 96-bit (12-byte) unique nonces
- Key ID tagging for zero-downtime key rotation
- Associated data (AAD) authentication binding key ID to ciphertext
"""

from __future__ import annotations

import base64
import hashlib
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings

settings = get_settings()


def get_master_key_bytes() -> bytes:
    """Retrieves 32-byte binary key from MASTER_KEY configuration."""
    key_str = settings.MASTER_KEY
    try:
        raw = base64.b64decode(key_str, validate=True)
        if len(raw) == 32:
            return raw
    except Exception:
        pass
    # Deterministic 32-byte key fallback for development placeholders
    return hashlib.sha256(key_str.encode("utf-8")).digest()


def encrypt_mfa_secret(secret_plaintext: str, key_id: str = "v1") -> bytes:
    """Encrypts MFA secret using AES-256-GCM tagged with key_id."""
    key = get_master_key_bytes()
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)
    aad = key_id.encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, secret_plaintext.encode("utf-8"), aad)
    # Format: {key_id}:{nonce_12_bytes}{ciphertext_with_tag}
    return f"{key_id}:".encode("utf-8") + nonce + ciphertext


def decrypt_mfa_secret(payload: bytes) -> str:
    """Decrypts AES-256-GCM payload using MASTER_KEY and verifies key_id."""
    key = get_master_key_bytes()
    aesgcm = AESGCM(key)
    colon_idx = payload.find(b":")
    if colon_idx == -1:
        # Backward compatibility fallback
        nonce = payload[:12]
        ciphertext = payload[12:]
        return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")

    key_id = payload[:colon_idx].decode("utf-8")
    nonce = payload[colon_idx + 1 : colon_idx + 13]
    ciphertext = payload[colon_idx + 13 :]
    aad = key_id.encode("utf-8")
    return aesgcm.decrypt(nonce, ciphertext, aad).decode("utf-8")
