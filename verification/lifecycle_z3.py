"""Standalone Z3 lifecycle invariant proof harness."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mnn.deterministic.formal import prove_lifecycle_invariants


def main() -> int:
    proof = prove_lifecycle_invariants()["z3"]
    print(json.dumps(proof, indent=2))
    return 0 if proof.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
