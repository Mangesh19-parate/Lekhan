"""RFC 9457 Problem Details error responses for Lekhan API."""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from app.shared.logging import get_correlation_id


class AppError(Exception):
    """Base domain application exception."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.errors = errors or []


def problem_json_response(
    status_code: int,
    code: str,
    detail: str,
    title: str | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    """Builds an RFC 9457 compliant application/problem+json response."""
    cid = get_correlation_id()
    if title is None:
        title = code.replace("_", " ").title()

    payload: dict[str, Any] = {
        "type": f"https://lekhan.local/errors/{code.lower()}",
        "title": title,
        "status": status_code,
        "code": code,
        "detail": detail,
        "correlation_id": cid,
    }
    if errors:
        payload["errors"] = errors

    return JSONResponse(
        status_code=status_code,
        content=payload,
        media_type="application/problem+json",
        headers={"X-Correlation-ID": cid},
    )
