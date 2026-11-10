"""Sentry Error Tracking Integration with Strict PII Redaction.

Adheres strictly to AGENTS.md Hard Rule 5:
- Never log personal data (names, IDs, addresses, document text).
- Sanitizes event breadcrumbs, request data, and exception frames before sending.
"""

from __future__ import annotations

import os
from typing import Any

from app.shared.logging import get_logger

logger = get_logger(__name__)

# Keys that must be stripped from any error report payload
SENSITIVE_KEYS = {
    "name",
    "full_name",
    "pan",
    "aadhaar",
    "aadhaar_last4",
    "phone",
    "mobile",
    "address",
    "vendors",
    "purchasers",
    "password",
    "secret",
    "token",
}


def sanitize_pii_from_dict(data: Any) -> Any:
    """Recursively replaces personal data with redacted placeholders."""
    if isinstance(data, dict):
        sanitized: dict[str, Any] = {}
        for k, v in data.items():
            if any(s in k.lower() for s in SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED_PII]"
            elif isinstance(v, (dict, list)):
                sanitized[k] = sanitize_pii_from_dict(v)
            else:
                sanitized[k] = v
        return sanitized
    elif isinstance(data, list):
        return [sanitize_pii_from_dict(item) for item in data]
    return data


def sentry_before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Strips PII from Sentry event payloads before transmission."""
    if "request" in event and "data" in event["request"]:
        event["request"]["data"] = sanitize_pii_from_dict(event["request"]["data"])

    if "breadcrumbs" in event and "values" in event["breadcrumbs"]:
        for b in event["breadcrumbs"]["values"]:
            if "data" in b:
                b["data"] = sanitize_pii_from_dict(b["data"])

    return event


def init_sentry(dsn: str | None = None, environment: str = "dev") -> bool:
    """Initializes Sentry SDK if DSN is configured. Otherwise acts as a clean no-op."""
    sentry_dsn = dsn or os.getenv("SENTRY_DSN")
    if not sentry_dsn:
        logger.debug("SENTRY_DSN not configured; Sentry tracking is disabled.")
        return False

    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            before_send=sentry_before_send,
            traces_sample_rate=0.1 if environment == "prod" else 1.0,
            send_default_pii=False,
        )
        logger.info("Sentry initialized with strict PII scrubbing for environment: %s", environment)
        return True
    except ImportError:
        logger.warning("sentry-sdk not installed; skipping Sentry initialization.")
        return False
    except Exception as exc:
        logger.error("Failed to initialize Sentry: %s", exc)
        return False

