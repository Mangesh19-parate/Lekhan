"""Human review queue for Kruti-to-Unicode converted templates.

Enforces:
- docs/PRD.md FR-06: Round-trip score tracked; reviewer sign-off per template; no auto-approval.
- docs/ARCHITECTURE.md §4.1: Output is a draft; a Marathi-literate reviewer signs off each template.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Literal

ReviewStatus = Literal["pending", "approved", "rejected"]


@dataclass
class ReviewQueueItem:
    """Individual template candidate in the review queue."""

    item_id: str
    source_file: str
    roundtrip_score: float
    status: ReviewStatus = "pending"
    latin_warnings: list[dict[str, Any]] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reviewer: str | None = None
    reviewed_at: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReviewQueue:
    """Manages the persistence and transition of conversion candidates."""

    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = storage_path or (
            Path(__file__).parent.parent / "work" / "conversion_review_queue.json"
        )
        self.items: dict[str, ReviewQueueItem] = {}
        self._load()

    def add_candidate(
        self,
        item_id: str,
        source_file: str,
        roundtrip_score: float,
        latin_warnings: list[dict[str, Any]] | None = None,
        anomalies: list[str] | None = None,
    ) -> ReviewQueueItem:
        """Enqueues a new converted template for human review."""
        item = ReviewQueueItem(
            item_id=item_id,
            source_file=source_file,
            roundtrip_score=roundtrip_score,
            status="pending",
            latin_warnings=latin_warnings or [],
            anomalies=anomalies or [],
        )
        self.items[item_id] = item
        self._save()
        return item

    def list_pending(self) -> list[ReviewQueueItem]:
        """Returns all items awaiting reviewer action."""
        return [i for i in self.items.values() if i.status == "pending"]

    def approve(self, item_id: str, reviewer: str, notes: str | None = None) -> ReviewQueueItem:
        """Approves a converted template. Requires human reviewer identification."""
        if not reviewer or reviewer.strip() == "":
            raise ValueError("Reviewer identity is required for approval (no auto-approval).")

        item = self.items.get(item_id)
        if not item:
            raise KeyError(f"Item '{item_id}' not found in review queue.")

        item.status = "approved"
        item.reviewer = reviewer
        item.reviewed_at = datetime.now(timezone.utc).isoformat()
        item.notes = notes
        self._save()
        return item

    def reject(self, item_id: str, reviewer: str, reason: str) -> ReviewQueueItem:
        """Rejects a converted template back for manual fix."""
        item = self.items.get(item_id)
        if not item:
            raise KeyError(f"Item '{item_id}' not found in review queue.")

        item.status = "rejected"
        item.reviewer = reviewer
        item.reviewed_at = datetime.now(timezone.utc).isoformat()
        item.notes = reason
        self._save()
        return item

    def get_summary(self) -> dict[str, Any]:
        """Returns total counts and average score."""
        scores = [i.roundtrip_score for i in self.items.values()]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        return {
            "total_candidates": len(self.items),
            "pending": len(self.list_pending()),
            "approved": len([i for i in self.items.values() if i.status == "approved"]),
            "rejected": len([i for i in self.items.values() if i.status == "rejected"]),
            "average_roundtrip_score": avg_score,
        }

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {k: v.to_dict() for k, v in self.items.items()}
        self.storage_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for k, v in raw.items():
                    self.items[k] = ReviewQueueItem(**v)
            except Exception:
                pass

