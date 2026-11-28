"""Template identifier validation and safe path resolution.

Prevents directory traversal, arbitrary file read/write, and symlink attacks:
- Enforces strict regex ^[a-z0-9_]{3,64}$
- Disallows NUL bytes and URL-encoded traversal (%2e%2e)
- Enforces path.is_relative_to(TEMPLATES_DIR)
- Rejects symlink template directories
"""

from __future__ import annotations

import re
import urllib.parse
from pathlib import Path

TEMPLATE_ID_PATTERN = re.compile(r"^[a-z0-9_]{3,64}$")
TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "templates-library"
).resolve()


def validate_template_id(template_id: str, base_dir: Path | None = None) -> Path:
    """Validates template_id against strict regex and directory traversal rules.

    Returns:
        Resolved target directory Path within base_dir (default: TEMPLATES_DIR).

    Raises:
        ValueError: If template_id is invalid or attempts path traversal.
    """
    if not isinstance(template_id, str):
        raise ValueError("template_id must be a string")

    if "\0" in template_id:
        raise ValueError("template_id contains forbidden NUL bytes")

    decoded = urllib.parse.unquote(template_id)
    if "\0" in decoded:
        raise ValueError("template_id contains forbidden NUL bytes")

    if not TEMPLATE_ID_PATTERN.fullmatch(template_id) or not TEMPLATE_ID_PATTERN.fullmatch(decoded):
        raise ValueError(f"Invalid template_id {template_id!r}: must match ^[a-z0-9_]{{3,64}}$")

    root = (base_dir or TEMPLATES_DIR).resolve()
    raw_target = root / template_id

    if raw_target.is_symlink():
        raise ValueError(f"Symlinks prohibited for template_id: {template_id!r}")

    target_path = raw_target.resolve()

    if not target_path.is_relative_to(root):
        raise ValueError(f"Path traversal detected in template_id: {template_id!r}")

    return target_path
