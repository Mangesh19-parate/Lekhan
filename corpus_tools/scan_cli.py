"""Developer CLI for offline DOCX linting and leftover client data scanning.

Usage:
    python -m corpus_tools.scan_cli path/to/template.docx [--manifest path/to/manifest.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from app.templates.lint.linter import DocxLinter


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan DOCX for leftover client data and lint errors.")
    parser.add_argument("docx_path", type=Path, help="Path to DOCX template file")
    parser.add_argument("--manifest", type=Path, default=None, help="Optional path to manifest.json")
    parser.add_argument("--json", action="store_true", help="Output report as JSON")
    args = parser.parse_args()

    if not args.docx_path.exists():
        print(f"Error: File '{args.docx_path}' does not exist.", file=sys.stderr)
        return 1

    manifest_data = None
    if args.manifest and args.manifest.exists():
        manifest_data = json.loads(args.manifest.read_text(encoding="utf-8"))

    docx_bytes = args.docx_path.read_bytes()
    linter = DocxLinter()
    report = linter.lint(docx_bytes, manifest=manifest_data)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.can_approve else 1

    print("=" * 60)
    print(f"DOCX LINT REPORT: {args.docx_path.name}")
    print(f"Can Approve: {'YES' if report.can_approve else 'NO (BLOCKING ISSUES)'}")
    print(f"Split Runs Repaired: {report.split_runs_repaired}")
    print(f"Fonts Found: {', '.join(report.fonts) if report.fonts else 'None'}")
    print("=" * 60)

    if report.leftover_data:
        print(f"\n[!] LEFTOVER CLIENT DATA FOUND ({len(report.leftover_data)} instances):")
        for idx, item in enumerate(report.leftover_data, 1):
            print(f"  {idx}. [{item.category}] {item.part} (para {item.paragraph_idx}): {item.masked_sample}")

    if report.errors:
        print(f"\n[X] ERRORS ({len(report.errors)}):")
        for idx, err in enumerate(report.errors, 1):
            print(f"  {idx}. [{err.code}] {err.message} ({err.part})")

    if report.warnings:
        print(f"\n[!] WARNINGS ({len(report.warnings)}):")
        for idx, w in enumerate(report.warnings, 1):
            print(f"  {idx}. [{w.code}] {w.message}")

    if report.is_clean:
        print("\n[OK] Template is clean: zero errors and zero leftover client data.")

    return 0 if report.can_approve else 1


if __name__ == "__main__":
    sys.exit(main())

