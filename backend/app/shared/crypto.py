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
import json
import re
import secrets
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings
from app.shared.logging import get_logger

logger = get_logger(__name__)
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


def encrypt_json_payload(payload: dict[str, Any] | list[Any], key_id: str = "v1") -> dict[str, Any]:
    """Encrypts an entire JSON dictionary or list into an authenticated AES-256-GCM envelope."""
    if not payload:
        return {}
    if isinstance(payload, dict) and "_enc" in payload and "_v" in payload:
        return payload
    raw_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    encrypted_bytes = encrypt_field(raw_json, key_id=key_id)
    b64_ciphertext = base64.b64encode(encrypted_bytes).decode("ascii")
    return {"_enc": b64_ciphertext, "_v": "1"}


def decrypt_json_payload(payload: Any) -> Any:
    """Decrypts an AES-256-GCM envelope dictionary back to the original dictionary or list."""
    if not isinstance(payload, dict):
        return payload
    if "_enc" not in payload or "_v" not in payload:
        return payload
    b64_ciphertext = payload["_enc"]
    try:
        encrypted_bytes = base64.b64decode(b64_ciphertext.encode("ascii"), validate=True)
        raw_json = decrypt_field(encrypted_bytes)
        return json.loads(raw_json)
    except Exception as exc:
        logger.error("Failed to decrypt JSON payload: %s", exc)
        from app.config import get_settings
        if get_settings().ENV in ("prod", "staging"):
            raise ValueError(f"Payload decryption failed: {exc}") from exc
        return payload
