"""Deterministic replay engine for audit logs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .audit import replay_and_validate_log
from .basile import generate_basile_volume
from .utils import sha256_hex


@dataclass
class ReplayResult:
    ok: bool
    final_hash: str
    errors: List[str]
    regenerated_hashes: List[str]


def replay_log(path: Path, assert_hash: str | None = None) -> ReplayResult:
    ok, errors, final_hash = replay_and_validate_log(path)
    regenerated: List[str] = []

    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            event = json.loads(line)
            payload: Dict[str, object] = event.get("payload", {})
            if payload.get("action") == "basile_generate":
                output = generate_basile_volume(
                    coordinate=int(payload["coordinate"]),
                    seed=int(payload["seed"]),
                    query=str(payload.get("query", "")),
                    volume_length=int(payload.get("volume_length", 1024)),
                )
                regenerated_hash = sha256_hex(output)
                regenerated.append(regenerated_hash)
                expected = payload.get("output_hash")
                if expected and regenerated_hash != expected:
                    errors.append(
                        f"event {event.get('event_id')}: output hash mismatch expected={expected} actual={regenerated_hash}"
                    )

    if assert_hash and final_hash != assert_hash:
        errors.append(f"final hash mismatch expected={assert_hash} actual={final_hash}")

    return ReplayResult(
        ok=len(errors) == 0 and ok,
        final_hash=final_hash,
        errors=errors,
        regenerated_hashes=regenerated,
    )
