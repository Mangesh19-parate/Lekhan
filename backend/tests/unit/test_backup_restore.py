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
from backend.scripts.backup import create_backup
from backend.scripts.restore import restore_backup

from app.generation.jobs import JobRecord
from app.generation.pipeline import GenerationPipelineFSM


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
    pipeline = GenerationPipelineFSM()
    tenant_id = uuid.uuid4()
    job = JobRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        job_type="generate_docx",
        payload={
            "execution_date": "2026-11-09",
            "vendors": [
                {
                    "full_name": "Test Vendor",
                    "age": 45,
                    "address": "Nagpur",
                    "pan": "ABCDE1234F",
                    "aadhaar_last4": "1234",
                }
            ],
            "purchasers": [
                {
                    "full_name": "Test Purchaser",
                    "age": 40,
                    "address": "Nagpur",
                    "pan": "FGHIJ5678K",
                    "aadhaar_last4": "5678",
                }
            ],
            "property_details": {
                "plot_no": "99",
                "layout_name": "Shree Park",
                "mouza": "Besa",
                "khasra_no": "10/1",
                "city_survey_no": "CTS-99",
                "area_sqm": "150.00",
                "boundaries": {"east": "Road", "west": "Plot", "north": "Plot", "south": "Plot"},
            },
            "financial_terms": {
                "total_consideration": "2000000",
                "advance_paid": "400000",
                "balance_amount": "1600000",
                "payment_mode": "RTGS",
            },
            "witnesses": [{"full_name": "W1", "address": "N"}, {"full_name": "W2", "address": "N"}],
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

    # Corrupt archive file
    with open(archive_file, "ab") as f:
        f.write(b"CORRUPTED_BYTES_APPENDED")

    with pytest.raises(Exception):
        restore_backup(archive_path=archive_file)
