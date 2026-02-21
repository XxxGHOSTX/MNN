"""CLI entry-point for the MNN automation agent.

Run with:
    python -m mnn.agent [--checks CHECK1,CHECK2,...] [--fail-fast] [--log PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mnn.agent.core import Agent, CheckStatus


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mnn-agent",
        description=(
            "MNN automation agent: discovers, validates, and reports on the "
            "health of the MNN repository."
        ),
    )
    parser.add_argument(
        "--checks",
        metavar="CHECK1,CHECK2",
        default=",".join(Agent.CHECK_ORDER),
        help=(
            "Comma-separated list of checks to run. "
            f"Available: {', '.join(Agent.CHECK_ORDER)}. "
            "Default: all checks."
        ),
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        default=False,
        help="Stop after the first failing check.",
    )
    parser.add_argument(
        "--log",
        metavar="PATH",
        default=None,
        help="Path to write the JSON run log (default: agent_run.log in repo root).",
    )
    parser.add_argument(
        "--repo-root",
        metavar="PATH",
        default=None,
        help="Repository root directory (default: auto-detected from this file's location).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    selected = [c.strip() for c in args.checks.split(",") if c.strip()]
    unknown = [c for c in selected if c not in Agent.CHECK_ORDER]
    if unknown:
        parser.error(f"Unknown check(s): {', '.join(unknown)}. Available: {', '.join(Agent.CHECK_ORDER)}")

    repo_root = Path(args.repo_root).resolve() if args.repo_root else None
    log_file = Path(args.log).resolve() if args.log else None

    agent = Agent(
        repo_root=repo_root,
        checks=selected,
        fail_fast=args.fail_fast,
        log_file=log_file,
    )

    result = agent.run()
    print(result.summary())

    if agent.log_file.exists():
        print(f"\nFull log written to: {agent.log_file}")

    return 0 if result.passed() else 1


if __name__ == "__main__":
    sys.exit(main())
