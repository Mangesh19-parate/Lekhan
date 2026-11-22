"""Cryptographic utilities for envelope and field encryption using AES-256-GCM.

Features:
- Authenticated AES-GCM encryption with 96-bit (12-byte) unique nonces
- Key ID tagging for zero-downtime key rotation
- Associated data (AAD) authentication binding key ID to ciphertext
- HMAC-SHA256 blind indexing for privacy-preserving equality queries
- PII masking helpers for PAN, Aadhaar, and phone numbers
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
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
    return encrypt_field(secret_plaintext, key_id=key_id)


def decrypt_mfa_secret(payload: bytes) -> str:
    """Decrypts AES-256-GCM payload using MASTER_KEY and verifies key_id."""
    return decrypt_field(payload)


def encrypt_field(plaintext: str, key_id: str = "v1") -> bytes:
    """Encrypts sensitive PII field (e.g. PAN, Contact, ID) using AES-256-GCM."""
    if not plaintext:
        return b""
    key = get_master_key_bytes()
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)
    aad = key_id.encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), aad)
    # Format: {key_id}:{nonce_12_bytes}{ciphertext_with_tag}
    return f"{key_id}:".encode("utf-8") + nonce + ciphertext


def decrypt_field(payload: bytes) -> str:
    """Decrypts AES-256-GCM payload and returns original plaintext string."""
    if not payload:
        return ""
    key = get_master_key_bytes()
    aesgcm = AESGCM(key)
    colon_idx = payload.find(b":")
    if colon_idx == -1:
        nonce = payload[:12]
        ciphertext = payload[12:]
        return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")

    key_id = payload[:colon_idx].decode("utf-8")
    nonce = payload[colon_idx + 1 : colon_idx + 13]
    ciphertext = payload[colon_idx + 13 :]
    aad = key_id.encode("utf-8")
    return aesgcm.decrypt(nonce, ciphertext, aad).decode("utf-8")


def compute_blind_index(plaintext: str) -> bytes:
    """Computes HMAC-SHA256 blind index for exact-match equality queries without exposing PII."""
    if not plaintext:
        return b""
    norm = plaintext.strip().upper()
    key = get_master_key_bytes()
    # Blind index domain separation salt
    salt = b"lekhan_blind_index_salt_v1"
    h = hmac.new(key, salt + norm.encode("utf-8"), hashlib.sha256)
    return h.digest()


def mask_pan(pan: str | None) -> str:
    """Masks Indian PAN (e.g. ABCDE1234F -> ABCDE****F)."""
    if not pan:
        return ""
    clean = pan.strip().upper()
    if len(clean) == 10:
        return f"{clean[:5]}****{clean[-1]}"
    return f"{clean[:2]}****" if len(clean) > 4 else "****"


def mask_aadhaar(aadhaar: str | None) -> str:
    """Masks Indian Aadhaar (e.g. 1234 5678 9012 -> **** **** 9012)."""
    if not aadhaar:
        return ""
    digits = re.sub(r"\D", "", aadhaar)
    if len(digits) == 12:
        return f"**** **** {digits[-4:]}"
    return "****"


def mask_phone(phone: str | None) -> str:
    """Masks phone number (e.g. 9876543210 -> ******3210)."""
    if not phone:
        return ""
    clean = re.sub(r"\D", "", phone)
    if len(clean) >= 10:
        return f"{'*' * (len(clean) - 4)}{clean[-4:]}"
    return "****"
