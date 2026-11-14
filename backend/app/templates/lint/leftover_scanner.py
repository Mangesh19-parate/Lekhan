"""Leftover client data and PII scanner for DOCX templates and draft outputs.

Enforces:
- AGENTS.md Hard Rules 1 & 5: No real personal data; never log raw PII.
- docs/PRD.md FR-07: Leftover-data lint blocks release.
- docs/MCP.md line 71: Reports categories, counts, paragraph locations, and masked samples.
"""

from __future__ import annotations

import io
import re
import zipfile
from xml.etree import ElementTree as ET

from app.templates.lint.models import LeftoverFinding

W_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# Regex patterns for sensitive Indian PII identifiers
PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
AADHAAR_REGEX = re.compile(r"\b[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}\b")
PHONE_REGEX = re.compile(r"\b(?:\+?91[ -]?)?[6-9]\d{9}\b")
IFSC_REGEX = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
PINCODE_REGEX = re.compile(r"\b[1-9]\d{5}\b")
UNTAGGED_DATE_REGEX = re.compile(
    r"\b(?:0?[1-9]|[12]\d|3[01])[-/.](?:0?[1-9]|1[012])[-/.](?:19|20)\d\d\b"
)
UNTAGGED_AMOUNT_REGEX = re.compile(
    r"(?:Rs\.?|रु\.?|INR)\s*([1-9]\d{0,2}(?:,\d{2})*,\d{3}|\b[1-9]\d{4,}\b)"
)

# Strips Jinja tags before scanning so variable placeholders are not flagged
JINJA_STRIPPER = re.compile(r"(\{\{[^}]*\}\}|\{%[^%]*%\})")


def mask_sensitive_value(value: str, category: str) -> str:
    """Returns privacy-safe redacted preview without exposing real data."""
    val = value.strip()
    if category == "PAN":
        return f"{val[:2]}***{val[-2:]}" if len(val) >= 4 else "PAN:***"
    if category == "AADHAAR":
        digits = re.sub(r"\D", "", val)
        return f"**** **** {digits[-4:]}" if len(digits) >= 4 else "UID:****"
    if category == "PHONE":
        digits = re.sub(r"\D", "", val)
        return f"+91 {digits[:2]}****{digits[-2:]}" if len(digits) >= 4 else "MOB:****"
    if category == "IFSC":
        return f"{val[:4]}0***" if len(val) >= 4 else "IFSC:****"
    if category == "PINCODE":
        return f"{val[:2]}**{val[-2:]}" if len(val) >= 4 else "PIN:****"
    if category == "AMOUNT":
        return "Rs. [HIGH_AMOUNT_LITERAL]"
    return "[REDACTED_LITERAL]"


def scan_docx_for_leftover_data(docx_bytes: bytes) -> list[LeftoverFinding]:
    """Scans all paragraph and table texts in DOCX for leftover client data and PII."""
    findings: list[LeftoverFinding] = []

    try:
        with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
            for info in zf.infolist():
                if info.filename.startswith("word/") and (
                    info.filename == "word/document.xml"
                    or "header" in info.filename
                    or "footer" in info.filename
                ):
                    content = zf.read(info.filename)
                    try:
                        root = ET.fromstring(content)
                        for p_idx, p in enumerate(root.iter(f"{{{W_NAMESPACE}}}p")):
                            raw_text = "".join(t.text or "" for t in p.iter(f"{{{W_NAMESPACE}}}t"))

                            # Strip valid Jinja tags so placeholders like {{ party.pan }} are not flagged
                            clean_text = JINJA_STRIPPER.sub(" ", raw_text)

                            # 1. PAN Scan
                            pan_matches = PAN_REGEX.findall(clean_text)
                            if pan_matches:
                                findings.append(
                                    LeftoverFinding(
                                        category="PAN",
                                        count=len(pan_matches),
                                        part=info.filename,
                                        paragraph_idx=p_idx,
                                        masked_sample=mask_sensitive_value(pan_matches[0], "PAN"),
                                    )
                                )

                            # 2. Aadhaar Scan
                            aadhaar_matches = AADHAAR_REGEX.findall(clean_text)
                            if aadhaar_matches:
                                findings.append(
                                    LeftoverFinding(
                                        category="AADHAAR",
                                        count=len(aadhaar_matches),
                                        part=info.filename,
                                        paragraph_idx=p_idx,
                                        masked_sample=mask_sensitive_value(
                                            aadhaar_matches[0], "AADHAAR"
                                        ),
                                    )
                                )

                            # 3. Phone Scan
                            phone_matches = PHONE_REGEX.findall(clean_text)
                            if phone_matches:
                                findings.append(
                                    LeftoverFinding(
                                        category="PHONE",
                                        count=len(phone_matches),
                                        part=info.filename,
                                        paragraph_idx=p_idx,
                                        masked_sample=mask_sensitive_value(
                                            phone_matches[0], "PHONE"
                                        ),
                                    )
                                )

                            # 4. IFSC Scan
                            ifsc_matches = IFSC_REGEX.findall(clean_text)
                            if ifsc_matches:
                                findings.append(
                                    LeftoverFinding(
                                        category="IFSC",
                                        count=len(ifsc_matches),
                                        part=info.filename,
                                        paragraph_idx=p_idx,
                                        masked_sample=mask_sensitive_value(ifsc_matches[0], "IFSC"),
                                    )
                                )

                            # 5. Untagged Large Financial Amounts
                            amt_matches = UNTAGGED_AMOUNT_REGEX.findall(clean_text)
                            if amt_matches:
                                findings.append(
                                    LeftoverFinding(
                                        category="AMOUNT",
                                        count=len(amt_matches),
                                        part=info.filename,
                                        paragraph_idx=p_idx,
                                        masked_sample=mask_sensitive_value(
                                            amt_matches[0], "AMOUNT"
                                        ),
                                    )
                                )

                    except (ET.ParseError, UnicodeDecodeError, KeyError):
                        continue

    except (zipfile.BadZipFile, OSError, KeyError):
        findings.append(
            LeftoverFinding(
                category="CORRUPT_ARCHIVE",
                count=1,
                part="archive",
                paragraph_idx=0,
                masked_sample="[MALFORMED_DOCX]",
            )
        )

    return findings
