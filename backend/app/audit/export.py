"""Signed audit trail export and cryptographic verification.

Adheres to:
- PRD G4 & FR-17: Tamper-evident audit trail export
- AGENTS.md Hard Rule 5: Zero personal data in logs or export
- Deterministic canonical JSON serialization with HMAC-SHA256 signature
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.audit.repository import AuditRecord


def format_audit_records(records: list[AuditRecord]) -> list[dict[str, Any]]:
    """Formats audit records into standardized dictionary representation."""
    formatted: list[dict[str, Any]] = []
    for r in records:
        formatted.append(
            {
                "id": r.id,
                "action": r.action,
                "entity": r.entity,
                "entity_id": r.entity_id,
                "timestamp": r.at.isoformat(),
                "actor_id": str(r.actor_id) if r.actor_id else None,
                "hash": r.hash.hex(),
                "prev_hash": r.prev_hash.hex() if r.prev_hash else "00" * 32,
                "meta": r.meta,
            }
        )
    return formatted


def create_signed_audit_export(
    tenant_id: uuid.UUID,
    records: list[AuditRecord],
    chain_valid: bool,
    secret_key: str,
) -> dict[str, Any]:
    """Generates an HMAC-SHA256 signed JSON audit export envelope."""
    formatted_records = format_audit_records(records)
    payload: dict[str, Any] = {
        "tenant_id": str(tenant_id),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(formatted_records),
        "chain_valid": chain_valid,
        "head_hash": formatted_records[-1]["hash"] if formatted_records else "00" * 32,
        "records": formatted_records,
    }

    canonical_bytes = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    signature = hmac.new(secret_key.encode("utf-8"), canonical_bytes, hashlib.sha256).hexdigest()

    return {
        "signature_algorithm": "HMAC-SHA256",
        "signature": signature,
        "payload": payload,
    }


def verify_signed_audit_export(
    signed_export: dict[str, Any],
    secret_key: str,
) -> bool:
    """Verifies HMAC-SHA256 signature and integrity of an exported audit trail."""
    if not isinstance(signed_export, dict):
        return False
    signature = signed_export.get("signature")
    payload = signed_export.get("payload")
    if not signature or not isinstance(payload, dict):
        return False

    canonical_bytes = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    expected_sig = hmac.new(secret_key.encode("utf-8"), canonical_bytes, hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, expected_sig)
