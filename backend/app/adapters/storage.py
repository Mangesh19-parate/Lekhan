"""Object store port and local filesystem adapter.

Adheres strictly to AGENTS.md Hard Rule 9 & ARCHITECTURE.md Section 5:
- Atomic file writes: write to unique .tmp file, flush, fsync, atomic os.replace/rename.
- Idempotent and crash-safe.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Protocol

from app.config import get_settings
from app.shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ObjectStore(Protocol):
    """Port interface for blob/file storage."""

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Stores bytes atomically under key and returns the reference key."""
        ...

    def get(self, key: str) -> bytes | None:
        """Retrieves raw bytes for key, or None if key does not exist."""
        ...

    def exists(self, key: str) -> bool:
        """Checks if a key exists in storage."""
        ...

    def delete(self, key: str) -> bool:
        """Deletes key from storage."""
        ...


class LocalObjectStore:
    """Local volume storage adapter with atomic write guarantees."""

    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or settings.STORAGE_PATH
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        """Resolves clean storage path, preventing directory traversal."""
        clean_key = key.replace("\\", "/").lstrip("/")
        path = (self.base_path / clean_key).resolve()
        if not str(path).startswith(str(self.base_path.resolve())):
            raise ValueError(f"Directory traversal detected in storage key: {key}")
        return path

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Atomically writes data to disk using temporary file, fsync, and rename."""
        target_path = self._resolve_path(key)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to sibling temp file in the same directory to guarantee atomic rename across filesystems
        temp_file = target_path.with_name(f".tmp_{uuid.uuid4().hex}_{target_path.name}")
        try:
            with open(temp_file, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())

            # Atomic replace
            os.replace(temp_file, target_path)
            return key
        except Exception:
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
            raise

    def get(self, key: str) -> bytes | None:
        """Reads bytes from storage."""
        target_path = self._resolve_path(key)
        if not target_path.exists() or not target_path.is_file():
            return None
        return target_path.read_bytes()

    def exists(self, key: str) -> bool:
        """Checks existence of file."""
        target_path = self._resolve_path(key)
        return target_path.exists() and target_path.is_file()

    def delete(self, key: str) -> bool:
        """Deletes file if exists."""
        target_path = self._resolve_path(key)
        if target_path.exists():
            target_path.unlink()
            return True
        return False


# Global default storage singleton
default_storage: ObjectStore = LocalObjectStore()
