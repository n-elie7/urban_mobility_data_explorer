import csv
from pathlib import Path

class TransparencyLog:
    def __init__(self):
        self.counts: dict[str, int] = {}
        self.nulled: dict[str, int] = {}
        self.total_in = 0
        self.total_out = 0

    def drop(self, reason: str, n: int) -> None:
        if n:
            if reason not in self.counts:
                self.counts[reason] = 0
            self.counts[reason] += int(n)

    def note_null(self, reason: str, n: int) -> None:
        if n:
            if reason not in self.nulled:
                self.nulled[reason] = 0
            self.nulled[reason] += int(n)

    def summary(self) -> dict:
        return {
            "rows_in": self.total_in,
            "rows_out": self.total_out,
            "rows_dropped": self.total_in - self.total_out,
            "by_reason": self.counts,
            "fields_nulled": self.nulled,
        }

    def write_csv(self, path: Path) -> None:
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["category", "reason", "count"])

            # Equivalent of Counter.most_common()
            for reason, n in sorted(
                self.counts.items(),
                key=lambda item: item[1],
                reverse=True
            ):
                w.writerow(["dropped_row", reason, n])

            for reason, n in sorted(
                self.nulled.items(),
                key=lambda item: item[1],
                reverse=True
            ):
                w.writerow(["nulled_field", reason, n])
