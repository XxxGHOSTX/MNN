"""Deterministic benchmark and drift validation suite."""

from __future__ import annotations

import json
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mnn.deterministic.basile import generate_basile_volume
from mnn.deterministic.utils import sha256_hex


def run_once(seed: int, coordinate: int, length: int) -> dict:
    started = time.perf_counter()
    text = generate_basile_volume(coordinate=coordinate, seed=seed, volume_length=length)
    elapsed = time.perf_counter() - started
    return {
        "elapsed_seconds": round(elapsed, 6),
        "output_hash": sha256_hex(text),
        "length": len(text),
    }


def main() -> int:
    cfg = {"seed": 2026, "coordinate": 424242, "length": 131200}
    run_a = run_once(**cfg)
    run_b = run_once(**cfg)
    drift = run_a["output_hash"] != run_b["output_hash"]

    report = {
        "config": cfg,
        "run_a": run_a,
        "run_b": run_b,
        "bit_for_bit_equal": not drift,
    }
    print(json.dumps(report, indent=2))
    return 1 if drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
