"""Deterministic output checker for pipeline reproducibility."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import run_pipeline


def digest_for_query(query: str) -> str:
    output = run_pipeline(query)
    payload = json.dumps(output, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    args = parser.parse_args()

    digest_a = digest_for_query(args.query)
    digest_b = digest_for_query(args.query)

    print(json.dumps({"query": args.query, "digest_a": digest_a, "digest_b": digest_b}, indent=2))

    if digest_a != digest_b:
        print("Deterministic check failed")
        return 1

    print("Deterministic check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
