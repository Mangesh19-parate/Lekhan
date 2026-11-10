"""Regression benchmark runner for Kruti Dev to Unicode conversion.

Evaluates:
1. Round-trip conversion score on all synthetic test files.
2. Latin-typed-in-Kruti detection accuracy.
3. Enqueues candidates into the human ReviewQueue.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from app.lang_packs.encodings.kruti import KrutiConverter
from corpus_tools.review_queue import ReviewQueue


def run_benchmark(samples_dir: Path | None = None) -> int:
    samples_dir = samples_dir or (
        Path(__file__).parent / "fixtures" / "synthetic_samples"
    )
    if not samples_dir.exists():
        print(f"Error: Samples directory not found at {samples_dir}", file=sys.stderr)
        return 1

    sample_files = sorted(samples_dir.glob("*.txt"))
    if not sample_files:
        print(f"Error: No sample files found in {samples_dir}", file=sys.stderr)
        return 1

    queue = ReviewQueue()
    scores: list[float] = []
    total_latin_warnings = 0

    print("=" * 75)
    print("KRUTI DEV TO UNICODE: CONVERTER HARDENING & BENCHMARK REPORT")
    print("=" * 75)
    print(f"{'Sample File':<42} | {'Score (%)':<10} | {'Latin Warnings':<15}")
    print("-" * 75)

    for sf in sample_files:
        raw_text = sf.read_text(encoding="utf-8")
        score, _, anomalies = KrutiConverter.compute_roundtrip_score(raw_text)
        latin_warnings = KrutiConverter.detect_latin_in_kruti(raw_text)

        scores.append(score)
        total_latin_warnings += len(latin_warnings)

        # Enqueue in review queue
        queue.add_candidate(
            item_id=sf.stem,
            source_file=sf.name,
            roundtrip_score=score,
            latin_warnings=[asdict(w) if hasattr(w, "__dict__") else {"text": str(w)} for w in latin_warnings],
            anomalies=anomalies,
        )

        warn_desc = f"{len(latin_warnings)} found" if latin_warnings else "clean"
        print(f"{sf.name:<42} | {score:>8.2f}% | {warn_desc:<15}")

    avg_score = round(sum(scores) / len(scores), 2)
    print("=" * 75)
    print(f"Total Samples Evaluated: {len(sample_files)}")
    print(f"Average Round-Trip Fidelity Score: {avg_score}%")
    print(f"Total Latin-in-Kruti Warnings Flagged: {total_latin_warnings}")
    print(f"Candidates Enqueued in Review Queue: {len(sample_files)}")
    print("=" * 75)

    # Threshold agreement check: candidate automated templates must achieve >= 98.0%
    if avg_score >= 98.0:
        print("\n[PASS] Corpus meets agreed Gate 1 -> Gate 2 accuracy threshold (>= 98.0%).")
        return 0
    else:
        print("\n[WARN] Corpus below agreed threshold (>= 98.0%). Manual review required.")
        return 1


if __name__ == "__main__":
    sys.exit(run_benchmark())

