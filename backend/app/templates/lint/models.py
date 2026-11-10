"""Data models and findings for DOCX template linting and leftover scanning."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LintSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class LintFinding:
    """Individual lint finding."""

    code: str
    severity: LintSeverity
    message: str
    part: str = "word/document.xml"
    paragraph_idx: int | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "part": self.part,
            "paragraph_idx": self.paragraph_idx,
            "meta": self.meta,
        }


@dataclass
class LeftoverFinding:
    """Finding for leftover real client data or PII patterns."""

    category: str  # PAN, AADHAAR, PHONE, PINCODE, IFSC, REAL_DATA
    count: int
    part: str
    paragraph_idx: int
    masked_sample: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "count": self.count,
            "part": self.part,
            "paragraph_idx": self.paragraph_idx,
            "masked_sample": self.masked_sample,
        }


@dataclass
class LintReport:
    """Comprehensive report produced by DocxLinter."""

    errors: list[LintFinding] = field(default_factory=list)
    warnings: list[LintFinding] = field(default_factory=list)
    leftover_data: list[LeftoverFinding] = field(default_factory=list)
    fonts: list[str] = field(default_factory=list)
    split_runs_repaired: int = 0
    can_approve: bool = True

    def add_finding(self, finding: LintFinding) -> None:
        if finding.severity == LintSeverity.ERROR:
            self.errors.append(finding)
            self.can_approve = False
        elif finding.severity == LintSeverity.WARNING:
            self.warnings.append(finding)

    def add_leftover(self, leftover: LeftoverFinding) -> None:
        self.leftover_data.append(leftover)
        self.can_approve = False  # Leftover data unconditionally blocks approval

    @property
    def is_clean(self) -> bool:
        return len(self.errors) == 0 and len(self.leftover_data) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_clean": self.is_clean,
            "can_approve": self.can_approve,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "leftover_data": [l.to_dict() for l in self.leftover_data],
            "fonts": self.fonts,
            "split_runs_repaired": self.split_runs_repaired,
        }
