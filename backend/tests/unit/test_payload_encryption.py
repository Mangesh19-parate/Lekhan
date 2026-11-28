"""Unit tests for JSON payload and PII encryption (AES-256-GCM)."""

from app.shared.crypto import (
    compute_blind_index,
    decrypt_json_payload,
    encrypt_json_payload,
    mask_aadhaar,
    mask_pan,
    mask_phone,
)


def test_encrypt_decrypt_json_payload_roundtrip() -> None:
    original = {
        "sellers": [
            {
                "full_name": "रमेश पाटील",
                "pan": "ABCDE1234F",
                "aadhaar": "1234 5678 9012",
                "phone": "9876543210",
                "address": "नागपूर, महाराष्ट्र",
            }
        ],
        "financial": {"total_consideration": 1500000},
    }

    # Encrypt
    encrypted = encrypt_json_payload(original)
    assert "_enc" in encrypted
    assert encrypted["_v"] == "1"
    # Ensure plaintext is not visible in envelope
    assert "रमेश" not in str(encrypted)
    assert "ABCDE1234F" not in str(encrypted)

    # Decrypt
    decrypted = decrypt_json_payload(encrypted)
    assert decrypted == original
    assert decrypted["sellers"][0]["full_name"] == "रमेश पाटील"
    assert decrypted["sellers"][0]["pan"] == "ABCDE1234F"


def test_decrypt_json_payload_backward_compatibility() -> None:
    # Plaintext JSON dict should pass through unchanged
    raw = {"doc_type": "sale_deed", "area": 150.0}
    result = decrypt_json_payload(raw)
    assert result == raw


def test_pii_masking_helpers() -> None:
    assert mask_pan("ABCDE1234F") == "ABCDE****F"
    assert mask_aadhaar("1234 5678 9012") == "**** **** 9012"
    assert mask_phone("9876543210") == "******3210"


def test_blind_index_deterministic() -> None:
    idx1 = compute_blind_index("ABCDE1234F")
    idx2 = compute_blind_index("abcde1234f ")
    assert idx1 == idx2
    assert len(idx1) == 32
