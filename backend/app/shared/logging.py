"""Structured logging with request-scoped correlation ID context.

Strict compliance with AGENTS.md Hard Rule 5:
Never log personal data (names, Aadhaar, PAN, addresses).
Log IDs, correlation IDs, timestamps, and error codes only.
"""

from __future__ import annotations

import contextvars
import logging
import sys

from app.shared.ids import uuid7_str

# Request-scoped correlation ID context variable
correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id",
    default="",
)


def get_correlation_id() -> str:
    """Retrieves the current request's correlation ID or initializes a new one."""
    cid = correlation_id_ctx.get()
    if not cid:
        cid = uuid7_str()
        correlation_id_ctx.set(cid)
    return cid


class CorrelationIdFilter(logging.Filter):
    """Injects current correlation_id into all logging.LogRecord instances."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_ctx.get() or "-"
        return True


def setup_logging(level: str = "INFO") -> None:
    """Configures root logger with correlation ID enrichment."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if not any(isinstance(f, CorrelationIdFilter) for f in root_logger.filters):
        root_logger.addFilter(CorrelationIdFilter())

    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [cid:%(correlation_id)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Returns a module logger with correlation ID support."""
    logger = logging.getLogger(name)
    logger.addFilter(CorrelationIdFilter())
    return logger
