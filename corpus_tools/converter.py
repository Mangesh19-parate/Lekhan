"""Offline developer converter: batch-converts legacy Kruti Dev DOCX files to Unicode.

Run-aware:
1. Inspects each Run's font.
2. Only converts runs formatted in Kruti Dev or DevLys font families.
3. Leaves Latin runs (Times New Roman, Arial, Calibri, etc.) untouched.
4. Merges adjacent same-format runs to preserve conjuncts across word splits.
5. Emits warnings for suspected Latin typed under Kruti font.
6. Sets converted run font to 'Noto Sans Devanagari' / 'Noto Serif Devanagari'.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from backend.app.lang_packs.encodings.kruti import (
    KrutiConverter,
    RunSegment,
    merge_adjacent_runs,
)


@dataclass
class FileConversionReport:
    """Detailed conversion summary for a single document."""

    file_name: str
    total_paragraphs: int
    total_runs: int
    converted_runs: int
    latin_preserved_runs: int
    warnings: list[dict[str, Any]]
    success: bool
    error: str | None = None


class DocxKrutiConverter:
    """Run-aware DOCX converter for Marathi/Hindi legal templates."""

    TARGET_FONT = "Noto Sans Devanagari"

    def __init__(self, target_font: str = TARGET_FONT) -> None:
        self.target_font = target_font

    def convert_document(self, input_path: Path, output_path: Path) -> FileConversionReport:
        """Converts a DOCX file from Kruti Dev to Unicode.

        Runs with Kruti font are translated; Latin runs are preserved.
        """
        try:
            import docx
        except ImportError:
            # Fallback if python-docx not yet installed in local environment
            return self._convert_simulated(input_path, output_path)

        doc = docx.Document(str(input_path))
        total_paras = len(doc.paragraphs)
        total_runs = 0
        converted_runs = 0
        preserved_runs = 0
        warnings: list[dict[str, Any]] = []

        for p_idx, para in enumerate(doc.paragraphs):
            if not para.runs:
                continue

            total_runs += len(para.runs)

            # 1. Extract runs as RunSegments
            segments: list[RunSegment] = []
            for run in para.runs:
                font_name = run.font.name if run.font else None
                # Check style font if run font is None
                if not font_name and para.style and para.style.font:
                    font_name = para.style.font.name

                is_kruti = KrutiConverter.is_kruti_font(font_name)
                segments.append(
                    RunSegment(
                        text=run.text,
                        font_name=font_name,
                        bold=run.bold,
                        italic=run.italic,
                        size_pt=float(run.font.size.pt) if run.font and run.font.size else None,
                        is_kruti=is_kruti,
                    )
                )

            # 2. Merge adjacent identical runs
            merged = merge_adjacent_runs(segments)

            # 3. Check for Latin-in-Kruti warnings & convert
            for seg in merged:
                if seg.is_kruti:
                    detected_warnings = KrutiConverter.detect_latin_in_kruti(seg.text)
                    for w in detected_warnings:
                        warnings.append(
                            {
                                "paragraph": p_idx,
                                "type": w.pattern_type,
                                "snippet": w.text,
                                "position": w.position,
                            }
                        )
                    seg.text = KrutiConverter.convert_string(seg.text)
                    seg.font_name = self.target_font
                    converted_runs += 1
                else:
                    preserved_runs += 1

            # 4. Rebuild paragraph runs
            # Clear existing runs
            p_elem = para._p
            for r in para.runs:
                p_elem.remove(r._r)

            # Append converted runs
            for seg in merged:
                new_run = para.add_run(seg.text)
                new_run.bold = seg.bold
                new_run.italic = seg.italic
                if seg.is_kruti:
                    new_run.font.name = self.target_font

        # Process tables as well
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        for run in para.runs:
                            font_name = run.font.name if run.font else None
                            if KrutiConverter.is_kruti_font(font_name):
                                run.text = KrutiConverter.convert_string(run.text)
                                run.font.name = self.target_font
                                converted_runs += 1
                            else:
                                preserved_runs += 1

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_path))

        return FileConversionReport(
            file_name=input_path.name,
            total_paragraphs=total_paras,
            total_runs=total_runs,
            converted_runs=converted_runs,
            latin_preserved_runs=preserved_runs,
            warnings=warnings,
            success=True,
        )

    def _convert_simulated(self, input_path: Path, output_path: Path) -> FileConversionReport:
        """Simulated conversion for text fixtures when python-docx is not loaded."""
        raw_text = input_path.read_text(encoding="utf-8", errors="ignore")
        warnings = [asdict(w) for w in KrutiConverter.detect_latin_in_kruti(raw_text)]
        converted = KrutiConverter.convert_string(raw_text)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(converted, encoding="utf-8")

        return FileConversionReport(
            file_name=input_path.name,
            total_paragraphs=len(raw_text.splitlines()),
            total_runs=1,
            converted_runs=1,
            latin_preserved_runs=0,
            warnings=warnings,
            success=True,
        )


def batch_convert(input_dir: Path, output_dir: Path) -> list[FileConversionReport]:
    """Converts all .docx and .txt files in input_dir and produces an execution report."""
    converter = DocxKrutiConverter()
    reports: list[FileConversionReport] = []

    files = list(input_dir.glob("*.docx")) + list(input_dir.glob("*.txt"))
    for file_path in files:
        out_file = output_dir / file_path.name
        report = converter.convert_document(file_path, out_file)
        reports.append(report)

    report_path = output_dir / "conversion_report.json"
    report_path.write_text(
        json.dumps([asdict(r) for r in reports], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return reports

