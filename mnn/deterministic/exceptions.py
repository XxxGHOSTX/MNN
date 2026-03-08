"""Deterministic exception primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class DeterministicHalt(RuntimeError):
    """Raised when deterministic lifecycle or invariant checks fail."""

    message: str
    snapshot: Dict[str, Any]

    def __str__(self) -> str:
        return f"{self.message} | snapshot={self.snapshot}"
