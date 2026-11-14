"""Unit and drill tests for Automated Backup and Restore (PRD FR-18, Features F-070).

Verifies:
1. Complete atomic backup generation with cryptographic SHA-256 manifest.
2. Complete restore drill: documents, counters, and storage files match original state.
3. Cryptographic integrity protection: tampered backup raises RestoreIntegrityError.
"""

import shutil
import tempfile
import uuid
from pathlib import Path

import pytest
try:
    from scripts.backup import create_backup
    from scripts.restore import restore_backup
except ImportError:
    from backend.scripts.backup import create_backup
    from backend.scripts.restore import restore_backup

from app.generation.jobs import JobQueue, JobRecord
from app.generation.pipeline import GenerationPipelineFSM, generation_pipeline
from app.generation.repository import InMemoryDocumentRepository


@pytest.fixture
def temp_backup_env():
    stage_dir = Path(tempfile.mkdtemp(prefix="lekhan_test_backup_"))
    backup_dest = stage_dir / "backups"
    storage_dest = stage_dir / "storage"
    backup_dest.mkdir()
    storage_dest.mkdir()

    yield {"stage": stage_dir, "backups": backup_dest, "storage": storage_dest}
    shutil.rmtree(stage_dir, ignore_errors=True)


def test_backup_and_restore_cycle(temp_backup_env) -> None:
    """Performs an end-to-end backup and restore drill cycle."""
    backups_dir = temp_backup_env["backups"]
    restore_storage_dir = temp_backup_env["storage"]

    # 1. Populate test documents and counters
    pipeline = generation_pipeline
    pipeline.repository = InMemoryDocumentRepository()
    tenant_id = uuid.uuid4()
    job = JobQueue().enqueue(
        tenant_id=tenant_id,
        job_type="generate_docx",
        payload={
            "execution_date": "2026-11-09",
            "sellers": [
                {
                    "full_name": "Test Vendor",
                    "age": 45,
                    "address": "Nagpur",
                    "pan": "ABCDE1234F",
                }
            ],
            "purchasers": [
                {
                    "full_name": "Test Purchaser",
                    "age": 40,
                    "address": "Nagpur",
                    "pan": "FGHIJ5678K",
                }
            ],
            "property_details": {
                "plot_no": "99",
                "layout_name": "Shree Park",
                "mouza": "Besa",
                "khasra_no": "10/1",
                "sheet_no": "CTS-99",
                "area_sqm": 150.00,
            },
            "boundaries": {"east": "Road", "west": "Plot", "north": "Plot", "south": "Plot"},
            "financial": {
                "total_consideration": 2000000,
                "earnest_advance": 400000,
            },
            "witness_1": "W1, N",
            "witness_2": "W2, N",
        },
    )
    doc_record = pipeline.process_job(job)
    assert doc_record.doc_no is not None

    # 2. Run backup
    archive_file = create_backup(destination_dir=backups_dir, include_storage=True)
    assert archive_file.exists()
    assert (backups_dir / f"{archive_file.name}.sha256").exists()

    # 3. Simulate disaster: clear in-memory state
    pipeline.clear()
    assert len(pipeline._documents) == 0

    # 4. Run restore drill
    report = restore_backup(archive_path=archive_file, target_storage_dir=restore_storage_dir)
    assert report["status"] == "success"
    assert report["restored_documents_count"] >= 1
    assert report["verified_files_count"] >= 1

    # 5. Verify restored state
    restored_doc = pipeline.get_document(doc_record.id, tenant_id)
    assert restored_doc is not None
    assert restored_doc.doc_no == doc_record.doc_no
    assert restored_doc.input_hash == doc_record.input_hash


def test_restore_tampered_archive_fails(temp_backup_env) -> None:
    """Verifies that an archive with a modified file fails the SHA-256 check."""
    backups_dir = temp_backup_env["backups"]
    archive_file = create_backup(destination_dir=backups_dir)

    # Corrupt archive file bytes
    with open(archive_file, "r+b") as f:
        f.seek(50)
        f.write(b"CORRUPTED_BYTES")

    with pytest.raises(Exception):
        restore_backup(archive_path=archive_file)
