"""CLI for batch-converting Kruti Dev files to Unicode."""

import argparse
import sys
from pathlib import Path

from corpus_tools.converter import batch_convert


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch convert Kruti Dev DOCX files to Unicode.")
    parser.add_argument("--input", required=True, type=Path, help="Input directory containing files")
    parser.add_argument("--output", required=True, type=Path, help="Output directory for converted files")

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input path {args.input} does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"Starting conversion from {args.input} to {args.output}...")
    reports = batch_convert(args.input, args.output)

    total_files = len(reports)
    total_warnings = sum(len(r.warnings) for r in reports)
    total_converted = sum(r.converted_runs for r in reports)
    total_preserved = sum(r.latin_preserved_runs for r in reports)

    print("\n--- Conversion Summary ---")
    print(f"Files Processed: {total_files}")
    print(f"Runs Converted (Kruti): {total_converted}")
    print(f"Runs Preserved (Latin): {total_preserved}")
    print(f"Latin-in-Kruti Warnings Flagged: {total_warnings}")
    print(f"Detailed Report: {args.output / 'conversion_report.json'}")


if __name__ == "__main__":
    main()

