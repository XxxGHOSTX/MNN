"""Deterministic zero-copy corpus processing engine."""

from __future__ import annotations

import mmap
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class DeterministicCorpusEngine:
    """mmap-based deterministic corpus processor."""

    path: Path

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        if not self.path.exists():
            raise FileNotFoundError(self.path)

    def ngram_counts(self, n: int = 5) -> List[Tuple[str, int]]:
        """Return sorted n-gram counts (stable ordering)."""
        if n <= 0:
            raise ValueError("n must be positive")

        counts: Counter[str] = Counter()
        with self.path.open("rb") as fh:
            with mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                total = len(mm)
                if total < n:
                    return []
                for offset in range(0, total - n + 1):
                    chunk = mm[offset : offset + n]
                    try:
                        gram = chunk.decode("ascii")
                    except UnicodeDecodeError:
                        continue
                    counts[gram] += 1
        return sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    def build_columnar_index(self, top_k: int = 256) -> Dict[str, object]:
        """Build a deterministic PyArrow-backed index if PyArrow is available."""
        rows = self.ngram_counts(n=5)[:top_k]
        try:
            import pyarrow as pa

            table = pa.table(
                {
                    "ngram": [row[0] for row in rows],
                    "count": [row[1] for row in rows],
                }
            )
            return {
                "backend": "pyarrow",
                "rows": len(rows),
                "schema": str(table.schema),
            }
        except Exception:
            return {
                "backend": "python-fallback",
                "rows": len(rows),
                "data": rows,
            }
