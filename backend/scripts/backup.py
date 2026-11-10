"""Automated Backup Utility for Lekhan (PRD FR-18, Features F-070, ARCHITECTURE.md Section 11).

Creates an atomic, checksummed backup bundle containing:
1. Database tables and counters snapshot.
2. Object store files (DOCX masters, templates, PDFs).
3. Cryptographic SHA-256 manifest with integrity verification.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.generation.pipeline import generation_pipeline
from app.numbering.service import document_numbering_service
from app.shared.logging import get_logger

logger = get_logger(__name__)


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hex digest of a file in 64KB chunks."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def create_backup(
    destination_dir: Path | None = None,
    include_storage: bool = True,
) -> Path:
    """Creates a complete timestamped, checksummed backup archive."""
    settings = get_settings()
    dest_dir = destination_dir or Path("./var/backups")
    dest_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    temp_stage = Path(tempfile.mkdtemp(prefix=f"backup_stage_{timestamp_str}_"))

    try:
        data_dir = temp_stage / "data"
        storage_stage_dir = temp_stage / "storage"
        data_dir.mkdir(parents=True, exist_ok=True)
        storage_stage_dir.mkdir(parents=True, exist_ok=True)

        manifest_entries: dict[str, str] = {}

        # 1. Snapshot database and in-memory services
        db_snapshot: dict[str, Any] = {
            "version": "1.0.0",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "documents": [
                {
                    "id": str(d.id),
                    "tenant_id": str(d.tenant_id),
                    "template_version_id": str(d.template_version_id),
                    "doc_no": d.doc_no,
                    "engine_version": d.engine_version,
                    "language": d.language,
                    "data_snapshot": d.data_snapshot,
                    "input_hash": d.input_hash.hex(),
                    "output_hash": d.output_hash.hex(),
                    "file_ref": d.file_ref,
                    "pdf_ref": d.pdf_ref,
                    "status": d.status,
                    "created_at": d.created_at,
                }
                for d in generation_pipeline._documents.values()
            ],
            "counters": [
                {
                    "tenant_id": str(k.tenant_id),
                    "series_key": k.series_key,
                    "year": k.year,
                    "value": v,
                }
                for k, v in document_numbering_service._counters.items()
            ],
        }

        db_file = data_dir / "db_snapshot.json"
        db_file.write_text(json.dumps(db_snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
        manifest_entries["data/db_snapshot.json"] = compute_sha256(db_file)

        # 2. Archive Object Store files
        storage_path = settings.STORAGE_PATH
        if include_storage and storage_path.exists():
            for root, _, files in os.walk(storage_path):
                for f in files:
                    if f.startswith(".tmp_"):
                        continue
                    src_f = Path(root) / f
                    rel_p = src_f.relative_to(storage_path)
                    dst_f = storage_stage_dir / rel_p
                    dst_f.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_f, dst_f)
                    manifest_entries[f"storage/{rel_p.as_posix()}"] = compute_sha256(dst_f)

        # 3. Write manifest.json
        manifest_path = temp_stage / "manifest.json"
        manifest_data = {
            "backup_version": "1.0.0",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "files_count": len(manifest_entries),
            "files": manifest_entries,
        }
        manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        # 4. Pack into compressed tar.gz
        archive_name = f"lekhan_backup_{timestamp_str}.tar.gz"
        archive_path = dest_dir / archive_name

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(manifest_path, arcname="manifest.json")
            tar.add(data_dir, arcname="data")
            if (temp_stage / "storage").exists():
                tar.add(storage_stage_dir, arcname="storage")

        archive_sha = compute_sha256(archive_path)
        sha_file = dest_dir / f"{archive_name}.sha256"
        sha_file.write_text(f"{archive_sha}  {archive_name}\n", encoding="utf-8")

        logger.info("Backup successfully created: %s (SHA-256: %s)", archive_path, archive_sha)
        return archive_path

    finally:
        shutil.rmtree(temp_stage, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lekhan Automated Backup Utility")
    parser.add_argument("--dest", type=Path, default=Path("./var/backups"), help="Destination directory for backups")
    args = parser.parse_args()
    created = create_backup(destination_dir=args.dest)
    print(f"Backup created at: {created}")

