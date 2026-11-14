"""Split-run tag detection and auto-merging for DOCX templates.

Word frequently breaks Jinja delimiters '{{', '}}', '{%', '%}' across multiple <w:r>
runs due to proofing flags or editing revisions. This utility:
1. Detects split tags within paragraph runs.
2. Auto-merges adjacent runs that share identical formatting (<w:rPr>).
3. Warns on split tags spanning conflicting formatting.
"""

from __future__ import annotations

import io
import re
import zipfile
from typing import TYPE_CHECKING, Any

import defusedxml.ElementTree as ET

from app.templates.lint.models import LintFinding, LintSeverity

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

W_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
TAG_SPLIT_REGEX = re.compile(r"(\{\{[^}]*\}\}|\{%[^%]*%\})")
START_DELIM = re.compile(r"(\{\{|\{%)")
END_DELIM = re.compile(r"(\}\}|%\})")


def get_run_pr_key(r_elem: Element | Any) -> str:
    """Returns canonical string representation of run formatting properties (<w:rPr>)."""
    r_pr = r_elem.find(f"{{{W_NAMESPACE}}}rPr")
    if r_pr is None:
        return ""
    return str(ET.tostring(r_pr, encoding="utf-8").decode("utf-8"))


def merge_paragraph_runs(p_elem: ET.Element) -> tuple[int, list[str]]:
    """Merges adjacent runs with identical formatting in a paragraph.

    Returns:
        (merge_count, list_of_conflicting_tags)
    """
    merge_count = 0
    conflicts: list[str] = []

    # Find all direct child runs
    children = list(p_elem)
    runs: list[tuple[int, ET.Element]] = [
        (idx, child) for idx, child in enumerate(children) if child.tag == f"{{{W_NAMESPACE}}}r"
    ]

    if len(runs) <= 1:
        return 0, []

    # Check if whole paragraph contains tags
    full_p_text = "".join(t.text or "" for t in p_elem.iter(f"{{{W_NAMESPACE}}}t"))
    if "{{" not in full_p_text and "{%" not in full_p_text:
        return 0, []

    # Merge adjacent runs with identical <w:rPr>
    i = 0
    while i < len(p_elem) - 1:
        r1 = p_elem[i]
        r2 = p_elem[i + 1]

        if r1.tag == f"{{{W_NAMESPACE}}}r" and r2.tag == f"{{{W_NAMESPACE}}}r":
            t1 = r1.find(f"{{{W_NAMESPACE}}}t")
            t2 = r2.find(f"{{{W_NAMESPACE}}}t")

            if t1 is not None and t2 is not None:
                pr1 = get_run_pr_key(r1)
                pr2 = get_run_pr_key(r2)

                if pr1 == pr2:
                    # Identical formatting: merge t2 into t1, preserve xml:space
                    t1_text = t1.text or ""
                    t2_text = t2.text or ""
                    combined = t1_text + t2_text
                    t1.text = combined
                    t1.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

                    # Remove r2
                    p_elem.remove(r2)
                    merge_count += 1
                    continue
                else:
                    # Check if a tag was split across this formatting boundary
                    if ("{" in (t1.text or "") and "}" in (t2.text or "")) or (
                        "%" in (t1.text or "") and "%" in (t2.text or "")
                    ):
                        conflicts.append(f"{t1.text} | {t2.text}")

        i += 1

    return merge_count, conflicts


def repair_and_check_split_runs(
    docx_bytes: bytes,
) -> tuple[bytes, int, list[LintFinding]]:
    """Inspects DOCX XML parts, auto-merges split runs, and reports findings.

    Returns:
        (repaired_docx_bytes, total_merges, findings)
    """
    findings: list[LintFinding] = []
    total_merges = 0
    out_buf = io.BytesIO()

    try:
        with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zin:
            with zipfile.ZipFile(out_buf, "w", compression=zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    content = zin.read(item.filename)

                    # Only process document, headers, footers
                    if item.filename.startswith("word/") and (
                        item.filename == "word/document.xml"
                        or "header" in item.filename
                        or "footer" in item.filename
                    ):
                        try:
                            root = ET.fromstring(content)
                            part_merges = 0

                            for p_idx, p in enumerate(root.iter(f"{{{W_NAMESPACE}}}p")):
                                m_count, conflicts = merge_paragraph_runs(p)
                                part_merges += m_count

                                for conflict in conflicts:
                                    findings.append(
                                        LintFinding(
                                            code="SPLIT_RUN_FORMATTING_CONFLICT",
                                            severity=LintSeverity.WARNING,
                                            message=f"Tag split across runs with different formatting: '{conflict}'.",
                                            part=item.filename,
                                            paragraph_idx=p_idx,
                                        )
                                    )

                            if part_merges > 0:
                                total_merges += part_merges
                                content = ET.tostring(root, encoding="utf-8")
                        except (ET.ParseError, UnicodeDecodeError, KeyError):
                            continue

                    zout.writestr(item, content)

        if total_merges > 0:
            findings.append(
                LintFinding(
                    code="SPLIT_RUNS_AUTO_MERGED",
                    severity=LintSeverity.INFO,
                    message=f"Successfully auto-merged {total_merges} split run(s).",
                    part="document",
                    meta={"merge_count": total_merges},
                )
            )

        return out_buf.getvalue(), total_merges, findings

    except (zipfile.BadZipFile, OSError) as exc:
        findings.append(
            LintFinding(
                code="SPLIT_RUN_PROCESSING_ERROR",
                severity=LintSeverity.ERROR,
                message=f"Failed to process runs: {exc}",
            )
        )
        return docx_bytes, 0, findings
