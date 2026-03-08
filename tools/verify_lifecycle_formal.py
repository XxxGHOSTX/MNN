"""Run lifecycle formal proofs and exit non-zero on failure."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mnn.deterministic.formal import prove_lifecycle_invariants


def main() -> int:
    result = prove_lifecycle_invariants()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("all_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
