"""
TradeCore — Import Pipeline: Report Generator

Collects all row results from an import run and produces:
  - A structured ImportReport object
  - A printable text summary (for CLI)
  - A JSON-serializable dict (for API/storage)

Report contains:
  - total rows processed
  - imported rows (ok + ok-with-warnings)
  - skipped rows (deduplication hits)
  - error rows (validation failures)
  - warning rows (imported but with warnings)
  - duplicate rows (same code appeared in batch or already in DB)
  - per-error-code breakdown
  - per-row detail (truncated to first N errors for large files)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .validators import Level, RowResult


@dataclass
class ImportReport:
    entity_type:    str
    source_file:    str
    import_run_id:  Optional[str] = None
    started_at:     datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at:   Optional[datetime] = None

    total_rows:    int = 0
    imported_rows: int = 0
    skipped_rows:  int = 0
    error_rows:    int = 0
    warning_rows:  int = 0
    duplicate_rows: int = 0

    # Detailed results (kept for first 1000 rows; trimmed for large files)
    row_results: List[RowResult] = field(default_factory=list)
    _max_stored_rows: int = 1000

    # Error code frequency map
    error_codes: Dict[str, int] = field(default_factory=dict)

    def add_row(self, result: RowResult) -> None:
        self.total_rows += 1

        # Count status
        if result.status == "ok":
            self.imported_rows += 1
        elif result.status == "warning":
            self.imported_rows += 1
            self.warning_rows += 1
        elif result.status == "error":
            self.error_rows += 1
        elif result.status == "skipped":
            self.skipped_rows += 1

        # Count duplicates specifically
        dup_msgs = [m for m in result.messages if m.code in ("DUPLICATE_IN_BATCH", "DUPLICATE_IN_DB")]
        if dup_msgs:
            self.duplicate_rows += 1

        # Tally error codes
        for msg in result.messages:
            if msg.level in (Level.ERROR, Level.WARNING):
                self.error_codes[msg.code] = self.error_codes.get(msg.code, 0) + 1

        # Store result (limit to _max_stored_rows)
        if len(self.row_results) < self._max_stored_rows:
            self.row_results.append(result)

    def finish(self) -> None:
        self.completed_at = datetime.now(timezone.utc)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return round((self.imported_rows / self.total_rows) * 100, 1)

    def to_dict(self) -> dict:
        return {
            "entity_type":    self.entity_type,
            "source_file":    self.source_file,
            "import_run_id":  self.import_run_id,
            "started_at":     self.started_at.isoformat(),
            "completed_at":   self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "summary": {
                "total_rows":     self.total_rows,
                "imported_rows":  self.imported_rows,
                "skipped_rows":   self.skipped_rows,
                "error_rows":     self.error_rows,
                "warning_rows":   self.warning_rows,
                "duplicate_rows": self.duplicate_rows,
                "success_rate_pct": self.success_rate,
            },
            "error_code_breakdown": self.error_codes,
            "rows": [r.to_dict() for r in self.row_results],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, default=str)

    def print_summary(self) -> str:
        """Returns a formatted text summary for CLI output."""
        sep = "─" * 60
        lines = [
            sep,
            f"IMPORT REPORT — {self.entity_type.upper()}",
            f"File         : {self.source_file}",
            f"Run ID       : {self.import_run_id or 'N/A'}",
            f"Duration     : {self.duration_seconds:.1f}s" if self.duration_seconds else "Duration     : N/A",
            sep,
            f"  Total rows       : {self.total_rows:>6}",
            f"  ✅ Imported       : {self.imported_rows:>6}  ({self.success_rate}%)",
            f"  ⚠️  With warnings  : {self.warning_rows:>6}",
            f"  ⏭️  Skipped        : {self.skipped_rows:>6}",
            f"  ❌ Errors         : {self.error_rows:>6}",
            f"  🔁 Duplicates     : {self.duplicate_rows:>6}",
            sep,
        ]

        if self.error_codes:
            lines.append("ERROR / WARNING CODE BREAKDOWN:")
            for code, count in sorted(self.error_codes.items(), key=lambda x: -x[1]):
                lines.append(f"  {code:<40} : {count:>4}x")
            lines.append(sep)

        # Show first 20 error rows
        error_rows = [r for r in self.row_results if r.has_errors][:20]
        if error_rows:
            lines.append(f"FIRST {len(error_rows)} ERROR ROWS:")
            for r in error_rows:
                lines.append(f"  Row {r.row_number:>4}:")
                for m in r.messages:
                    if m.level == Level.ERROR:
                        prefix = "    ❌"
                    elif m.level == Level.WARNING:
                        prefix = "    ⚠️"
                    else:
                        prefix = "    ℹ️"
                    lines.append(f"{prefix} [{m.code}] {m.field}: {m.message}")
            lines.append(sep)

        return "\n".join(lines)
