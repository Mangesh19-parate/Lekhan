"""Master DOCX Template Linter.

Orchestrates:
1. Structural safety checks (zip bomb, macros, external relationships, safe XML)
2. Split-run detection & auto-merging
3. Tag alignment against manifest (undefined tags vs unused fields)
4. Leftover client data / PII detection
5. Font auditing & legacy Kruti font rejection
"""

from __future__ import annotations

from typing import Any

from app.templates.lint.fonts import audit_docx_fonts
from app.templates.lint.leftover_scanner import scan_docx_for_leftover_data
from app.templates.lint.models import LintReport
from app.templates.lint.split_runs import repair_and_check_split_runs
from app.templates.lint.structural import check_structural_safety
from app.templates.lint.tag_checker import check_tag_alignment


class DocxLinter:
    """Production linter for legal DOCX templates and draft outputs."""

    def lint(self, docx_bytes: bytes, manifest: dict[str, Any] | None = None) -> LintReport:
        """Executes full linting suite and produces a LintReport."""
        _, report = self.lint_and_repair(docx_bytes, manifest)
        return report

    def lint_and_repair(
        self, docx_bytes: bytes, manifest: dict[str, Any] | None = None
    ) -> tuple[bytes, LintReport]:
        """Runs lint checks and auto-repairs split runs.

        Returns:
            (repaired_docx_bytes, lint_report)
        """
        report = LintReport()

        # 1. Structural safety checks
        structural_findings = check_structural_safety(docx_bytes)
        for finding in structural_findings:
            report.add_finding(finding)

        # Fatal structural flaws abort further processing
        if any(
            f.code in ("FILE_TOO_LARGE", "ZIP_BOMB_DETECTED", "CORRUPT_ZIP_ARCHIVE")
            for f in structural_findings
        ):
            return docx_bytes, report

        # 2. Split-run detection & auto-merging
        repaired_bytes, merge_count, split_findings = repair_and_check_split_runs(docx_bytes)
        report.split_runs_repaired = merge_count
        for finding in split_findings:
            report.add_finding(finding)

        # Use repaired bytes for subsequent inspections
        inspected_bytes = repaired_bytes

        # 3. Tag alignment against manifest
        if manifest:
            tag_findings = check_tag_alignment(inspected_bytes, manifest)
            for finding in tag_findings:
                report.add_finding(finding)

        # 4. Leftover client data / PII scanning
        leftover_findings = scan_docx_for_leftover_data(inspected_bytes)
        for leftover in leftover_findings:
            report.add_leftover(leftover)

        # 5. Font auditing
        fonts, font_findings = audit_docx_fonts(inspected_bytes)
        report.fonts = fonts
        for finding in font_findings:
            report.add_finding(finding)

        return repaired_bytes, report


default_linter = DocxLinter()
