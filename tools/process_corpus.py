"""Deterministic mmap corpus processing CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mnn.deterministic.corpus import DeterministicCorpusEngine


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    parser.add_argument("--top-k", type=int, default=20)
    args = parser.parse_args()

    engine = DeterministicCorpusEngine(args.path)
    ngrams = engine.ngram_counts(n=5)[: args.top_k]
    index = engine.build_columnar_index(top_k=args.top_k)
    print(json.dumps({"top_ngrams": ngrams, "index": index}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
