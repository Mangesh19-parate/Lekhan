"""Font auditing and legacy encoding detection for DOCX templates.

Verifies:
1. Rejects legacy Kruti Dev / DevLys fonts in approved templates (must be Unicode).
2. Audits all fonts used across document body, styles, and font table.
3. Verifies approved Devanagari fonts (Noto Serif Devanagari / Mangal).
"""

from __future__ import annotations

import io
import re
import zipfile
from xml.etree import ElementTree as ET

from app.templates.lint.models import LintFinding, LintSeverity

W_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

KRUTI_DEV_PATTERN = re.compile(
    r"(?:kruti\s*dev|devlys|shivaji|shree\s*lipi|apsara|chanakya)",
    re.IGNORECASE,
)

APPROVED_DEVANAGARI_FONTS = frozenset(
    {
        "noto serif devanagari",
        "noto sans devanagari",
        "mangal",
        "aparajita",
        "kokila",
        "nirmala ui",
    }
)


def audit_docx_fonts(docx_bytes: bytes) -> tuple[list[str], list[LintFinding]]:
    """Inspects DOCX for all referenced fonts and flags legacy Kruti Dev fonts."""
    findings: list[LintFinding] = []
    found_fonts: set[str] = set()

    try:
        with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
            for info in zf.infolist():
                if info.filename.startswith("word/") and (
                    info.filename in ("word/document.xml", "word/styles.xml", "word/fontTable.xml")
                    or "header" in info.filename
                    or "footer" in info.filename
                ):
                    content = zf.read(info.filename)
                    try:
                        root = ET.fromstring(content)
                        for r_fonts in root.iter(f"{{{W_NAMESPACE}}}rFonts"):
                            for attr_name in ("ascii", "cs", "hAnsi", "eastAsia"):
                                font_name = r_fonts.attrib.get(f"{{{W_NAMESPACE}}}{attr_name}")
                                if font_name:
                                    font_name_clean = font_name.strip()
                                    found_fonts.add(font_name_clean)

                                    # Check for prohibited Kruti Dev legacy fonts
                                    if KRUTI_DEV_PATTERN.search(font_name_clean):
                                        findings.append(
                                            LintFinding(
                                                code="LEGACY_FONT_KRUTI_FOUND",
                                                severity=LintSeverity.ERROR,
                                                message=(
                                                    f"Prohibited legacy Kruti font '{font_name_clean}' detected in '{info.filename}'. "
                                                    f"Approved templates must use canonical Unicode fonts (Noto Serif Devanagari / Mangal)."
                                                ),
                                                part=info.filename,
                                                meta={"font": font_name_clean},
                                            )
                                        )

                    except (ET.ParseError, UnicodeDecodeError, KeyError):
                        continue

    except (zipfile.BadZipFile, OSError, KeyError):
        findings.append(
            LintFinding(
                code="MALFORMED_DOCX",
                severity=LintSeverity.ERROR,
                message="Template DOCX archive could not be read for font inspection.",
            )
        )

    # Check for recommended Devanagari font presence if Devanagari text is expected
    sorted_fonts = sorted(found_fonts)
    has_approved_devanagari = any(f.lower() in APPROVED_DEVANAGARI_FONTS for f in sorted_fonts)
    if not has_approved_devanagari and sorted_fonts:
        findings.append(
            LintFinding(
                code="NO_APPROVED_DEVANAGARI_FONT",
                severity=LintSeverity.WARNING,
                message="No standard Devanagari font (Noto Serif Devanagari or Mangal) was found in font definitions.",
                part="word/fontTable.xml",
            )
        )

    return sorted_fonts, findings
