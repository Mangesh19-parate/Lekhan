"""Structural safety checks for DOCX template packages.

Defends against:
- Zip bombs (decompression ratio and size limits)
- Macro-enabled malicious files (.docm / vbaProject.bin)
- External relationship exfiltration (TargetMode="External")
- XML external entity expansion (XXE / DTD injection)
"""

from __future__ import annotations

import io
import re
import zipfile
from xml.etree import ElementTree as ET

from app.templates.lint.models import LintFinding, LintSeverity

MAX_COMPRESSED_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB (docs/API.md)
MAX_UNCOMPRESSED_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_COMPRESSION_RATIO = 100.0  # 100:1 ratio limit

MACRO_PATTERNS = frozenset(
    {
        "word/vbaProject.bin",
        "word/vbaData.xml",
        "word/vbaProjectSignature.bin",
    }
)

DANGEROUS_XML_PATTERNS = [
    re.compile(rb"<!DOCTYPE", re.IGNORECASE),
    re.compile(rb"<!ENTITY", re.IGNORECASE),
    re.compile(rb"SYSTEM\s+[\"']", re.IGNORECASE),
]


class StructuralLintError(ValueError):
    """Raised when structural validation completely halts document processing."""


def check_structural_safety(docx_bytes: bytes) -> list[LintFinding]:
    """Runs all structural safety checks on DOCX zip container."""
    findings: list[LintFinding] = []

    # 1. Compressed file size check
    if len(docx_bytes) > MAX_COMPRESSED_SIZE_BYTES:
        findings.append(
            LintFinding(
                code="FILE_TOO_LARGE",
                severity=LintSeverity.ERROR,
                message=f"DOCX file size ({len(docx_bytes)} bytes) exceeds 5 MB limit.",
                part="container",
            )
        )
        return findings

    # 2. Inspect ZIP structure & Decompression ratio
    try:
        with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
            total_uncompressed = 0
            for info in zf.infolist():
                total_uncompressed += info.file_size

                # Check individual file compression ratio
                if info.compress_size > 0:
                    ratio = info.file_size / info.compress_size
                    if ratio > MAX_COMPRESSION_RATIO and info.file_size > 100_000:
                        findings.append(
                            LintFinding(
                                code="ZIP_BOMB_DETECTED",
                                severity=LintSeverity.ERROR,
                                message=f"Entry '{info.filename}' has dangerous compression ratio ({ratio:.1f}:1).",
                                part=info.filename,
                            )
                        )
                        return findings

                # 3. Check for Macros / VBA binaries
                if info.filename.lower() in MACRO_PATTERNS or info.filename.endswith(".bin"):
                    findings.append(
                        LintFinding(
                            code="MACRO_ENABLED_FILE",
                            severity=LintSeverity.ERROR,
                            message=f"Macro-enabled template rejected: contains '{info.filename}'.",
                            part=info.filename,
                        )
                    )

            if total_uncompressed > MAX_UNCOMPRESSED_SIZE_BYTES:
                findings.append(
                    LintFinding(
                        code="TOTAL_UNCOMPRESSED_TOO_LARGE",
                        severity=LintSeverity.ERROR,
                        message=f"Total uncompressed size ({total_uncompressed} bytes) exceeds 50 MB limit.",
                        part="container",
                    )
                )
                return findings

            # 4. Check External Relationships in .rels
            for info in zf.infolist():
                if info.filename.endswith(".rels"):
                    content = zf.read(info.filename)
                    if b'TargetMode="External"' in content:
                        findings.append(
                            LintFinding(
                                code="EXTERNAL_RELATIONSHIP_FOUND",
                                severity=LintSeverity.ERROR,
                                message=f"External relationship detected in '{info.filename}'. External links are prohibited.",
                                part=info.filename,
                            )
                        )

            # 5. Check Safe XML (XXE / DTD protection)
            for info in zf.infolist():
                if info.filename.endswith(".xml"):
                    content = zf.read(info.filename)
                    for pat in DANGEROUS_XML_PATTERNS:
                        if pat.search(content):
                            findings.append(
                                LintFinding(
                                    code="UNSAFE_XML_DTD",
                                    severity=LintSeverity.ERROR,
                                    message=f"XML entity or DTD declaration found in '{info.filename}'.",
                                    part=info.filename,
                                )
                            )
                            break

    except zipfile.BadZipFile:
        findings.append(
            LintFinding(
                code="CORRUPT_ZIP_ARCHIVE",
                severity=LintSeverity.ERROR,
                message="Invalid or corrupt DOCX archive.",
                part="container",
            )
        )

    return findings


def strip_external_relationships(docx_bytes: bytes) -> bytes:
    """Sanitizes DOCX by stripping any external relationships from .rels files."""
    out_buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zin:
        with zipfile.ZipFile(out_buf, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.endswith(".rels") and b'TargetMode="External"' in data:
                    try:
                        root = ET.fromstring(data)
                        # Remove nodes with TargetMode == "External"
                        to_remove = [
                            elem for elem in root if elem.attrib.get("TargetMode") == "External"
                        ]
                        for elem in to_remove:
                            root.remove(elem)
                        data = ET.tostring(root, encoding="utf-8")
                    except (ET.ParseError, UnicodeDecodeError, KeyError):
                        continue
                zout.writestr(item, data)
    return out_buf.getvalue()
