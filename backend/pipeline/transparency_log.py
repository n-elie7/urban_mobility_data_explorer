"""Records every exclusion so the report can account for dropped rows."""

import csv
from collections import Counter
from pathlib import Path

class TransparencyLog:
    def __init__(self):
        self.counts: Counter = Counter()
        self.nulled: Counter = Counter()
        self.total_in = 0
        self.total_out = 0

    def drop(self, reason: str, n: int) -> None:
        if n:
            self.counts[reason] += int(n)

    def note_null(self, reason: str, n: int) -> None:
        """A field was set to NULL (e.g. unknown code) but the row was kept."""
        if n:
            self.nulled[reason] += int(n)

    def summary(self) -> dict:
        return {
            "rows_in": self.total_in,
            "rows_out": self.total_out,
            "rows_dropped": self.total_in - self.total_out,
            "by_reason": dict(self.counts),
            "fields_nulled": dict(self.nulled),
        }

    def write_csv(self, path: Path) -> None:
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["category", "reason", "count"])
            for reason, n in self.counts.most_common():
                w.writerow(["dropped_row", reason, n])
            for reason, n in self.nulled.most_common():
                w.writerow(["nulled_field", reason, n])
