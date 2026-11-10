"""DOCX template linting and leftover scanning package."""

from app.templates.lint.linter import DocxLinter, default_linter
from app.templates.lint.models import (
    LeftoverFinding,
    LintFinding,
    LintReport,
    LintSeverity,
)

__all__ = [
    "DocxLinter",
    "LeftoverFinding",
    "LintFinding",
    "LintReport",
    "LintSeverity",
    "default_linter",
]

