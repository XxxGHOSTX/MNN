"""Thalos deterministic CLI utilities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mnn.deterministic.basile import coordinate_to_base29, generate_basile_volume
from mnn.deterministic.replay import replay_log
from mnn.deterministic.utils import sha256_hex


def cmd_replay(args: argparse.Namespace) -> int:
    result = replay_log(args.log, assert_hash=args.assert_hash)
    print(
        json.dumps(
            {
                "ok": result.ok,
                "final_hash": result.final_hash,
                "errors": result.errors,
                "regenerated_hashes": result.regenerated_hashes,
            },
            indent=2,
        )
    )
    return 0 if result.ok else 1


def cmd_generate(args: argparse.Namespace) -> int:
    text = generate_basile_volume(
        coordinate=args.coordinate,
        seed=args.seed,
        query=args.query,
        volume_length=args.length,
    )
    print(
        json.dumps(
            {
                "coordinate": args.coordinate,
                "base29": coordinate_to_base29(args.coordinate),
                "seed": args.seed,
                "length": args.length,
                "output_hash": sha256_hex(text),
                "preview": text[:200],
            },
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="thalos", description="Deterministic Thalos tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    replay = subparsers.add_parser("replay", help="Replay and verify hash-chained JSONL logs")
    replay.add_argument("--log", required=True)
    replay.add_argument("--assert-hash", required=False)
    replay.set_defaults(func=cmd_replay)

    generate = subparsers.add_parser("generate", help="Generate deterministic Basile coordinate output")
    generate.add_argument("--coordinate", type=int, required=True)
    generate.add_argument("--seed", type=int, required=True)
    generate.add_argument("--query", default="")
    generate.add_argument("--length", type=int, default=4096)
    generate.set_defaults(func=cmd_generate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
