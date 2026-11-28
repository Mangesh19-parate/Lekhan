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


class CorrelationIdFormatter(logging.Formatter):
    """Safely injects default correlation_id if missing on foreign or propagated log records."""

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "correlation_id") or not record.correlation_id:
            record.correlation_id = correlation_id_ctx.get() or "-"
        return super().format(record)


def setup_logging(level: str = "INFO") -> None:
    """Configures root logger with correlation ID enrichment."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    cid_filter = CorrelationIdFilter()
    if not any(isinstance(f, CorrelationIdFilter) for f in root_logger.filters):
        root_logger.addFilter(cid_filter)

    formatter = CorrelationIdFormatter(
        fmt="%(asctime)s [%(levelname)s] [cid:%(correlation_id)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if not root_logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.addFilter(cid_filter)
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)
    else:
        for existing_handler in root_logger.handlers:
            if not any(isinstance(f, CorrelationIdFilter) for f in existing_handler.filters):
                existing_handler.addFilter(cid_filter)
            existing_handler.setFormatter(formatter)


def get_logger(name: str) -> logging.Logger:
    """Returns a module logger with correlation ID support."""
    logger = logging.getLogger(name)
    logger.addFilter(CorrelationIdFilter())
    return logger
