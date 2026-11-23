"""Network utility functions for client IP resolution and trusted proxy enforcement."""

from __future__ import annotations

import ipaddress
from fastapi import Request

from app.config import get_settings


def _is_ip_trusted(socket_ip: str, allowed_proxies: set[str]) -> bool:
    """Checks whether the socket IP matches an allowed IP literal or CIDR network block."""
    if socket_ip in allowed_proxies:
        return True
    try:
        addr = ipaddress.ip_address(socket_ip)
        for allowed in allowed_proxies:
            if "/" in allowed:
                try:
                    if addr in ipaddress.ip_network(allowed, strict=False):
                        return True
                except ValueError:
                    pass
    except ValueError:
        pass
    return False


def get_client_ip(request: Request, trusted_proxies: list[str] | None = None) -> str:
    """Extracts client IP safely, honoring X-Forwarded-For ONLY from trusted reverse proxies.

    If the request socket peer is not in trusted_proxies, X-Forwarded-For is strictly
    ignored to prevent IP spoofing and rate-limiting bypass.
    In dev/test mode, 'testclient' is permitted as a test proxy peer, but strictly
    excluded in production/staging environments.
    """
    socket_ip = request.client.host if request.client else "127.0.0.1"

    settings = get_settings()
    allowed_proxies = set(trusted_proxies if trusted_proxies is not None else settings.TRUSTED_PROXIES)
    if settings.is_dev or settings.is_test:
        allowed_proxies.add("testclient")

    if _is_ip_trusted(socket_ip, allowed_proxies):
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            first_ip = xff.split(",")[0].strip()
            if first_ip:
                return first_ip

    return socket_ip
