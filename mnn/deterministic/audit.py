"""Hash-chained JSONL audit log and replay verification."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .utils import canonical_json, sha256_hex


@dataclass
class HashChainAuditLogger:
    """Append-only hash-chained JSONL logger."""

    path: Path
    previous_hash: str = "0" * 64

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = {
            "event_id": event_id,
            "payload": payload,
            "state_chain_prev": self.previous_hash,
        }
        body_hash = sha256_hex(canonical_json(body))
        line = {**body, "state_chain_hash": body_hash}
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(canonical_json(line) + "\n")
        self.previous_hash = body_hash
        return line


def _iter_lines(path: Path) -> Iterable[Dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            yield json.loads(line)


def replay_and_validate_log(path: Path) -> Tuple[bool, List[str], str]:
    """Verify hash chain integrity and return final digest."""
    expected_prev = "0" * 64
    errors: List[str] = []
    final_hash = expected_prev

    for idx, row in enumerate(_iter_lines(path), start=1):
        if idx > 1 and row.get("state_chain_prev") == "0" * 64:
            # Run boundary: allow chain reset between independent executions.
            expected_prev = "0" * 64

        if row.get("state_chain_prev") != expected_prev:
            errors.append(f"line {idx}: invalid previous hash link")
        body = {
            "event_id": row.get("event_id"),
            "payload": row.get("payload"),
            "state_chain_prev": row.get("state_chain_prev"),
        }
        actual_hash = sha256_hex(canonical_json(body))
        if actual_hash != row.get("state_chain_hash"):
            errors.append(f"line {idx}: digest mismatch")
        expected_prev = row.get("state_chain_hash", expected_prev)
        final_hash = expected_prev

    return (len(errors) == 0, errors, final_hash)
