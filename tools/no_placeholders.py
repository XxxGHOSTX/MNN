#!/usr/bin/env python3
"""Placeholder scanner — no-placeholder enforcement gate.

Scans tracked source files for banned placeholder markers and exits non-zero
if any are found.  Designed to be run in CI and locally before every push.

Usage
-----
    python tools/no_placeholders.py [--root <repo-root>] [--allowlist <path>]

Exit codes
----------
    0 — no violations found
    1 — one or more violations found (details printed to stdout)
    2 — configuration or filesystem error

Allowlist
---------
Intentional occurrences (e.g. documentation examples that must literally
contain a banned word) can be suppressed by adding entries to
``tools/no_placeholders_allowlist.json``.  Each entry must include a
``justification`` field explaining why the exception is necessary.

Example allowlist entry::

    {
      "path": "docs/examples/bad_practices.md",
      "line": 42,
      "marker": "TODO",
      "justification": "Example showing what NOT to write in the tutorial"
    }

The allowlist is intentionally strict: only exact (path, line, marker) triples
are suppressed.  Broad file-level exclusions are not supported.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BANNED_PATTERNS: dict[str, re.Pattern[str]] = {
    "TODO": re.compile(r"\bTODO\b", re.IGNORECASE),
    "FIXME": re.compile(r"\bFIXME\b", re.IGNORECASE),
    "STUB": re.compile(r"\bSTUB\b", re.IGNORECASE),
    "MOCK": re.compile(r"\bMOCK\b", re.IGNORECASE),
    "PLACEHOLDER": re.compile(r"\bPLACEHOLDER\b", re.IGNORECASE),
    "TBD": re.compile(r"\bTBD\b", re.IGNORECASE),
    "HACK": re.compile(r"\bHACK\b", re.IGNORECASE),
    # XXX as a standalone comment marker — word-boundary avoids false positives
    # with legitimate data strings (e.g. DNA-like test sequences such as
    # "XXXXtestXXXX" which are NOT word-boundary isolated).
    "XXX": re.compile(r"\bXXX\b"),
}

SCANNED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".go",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".md",
        ".yml",
        ".yaml",
        ".toml",
        ".ini",
        ".cfg",
        ".sh",
        ".bash",
        "Makefile",
        "Dockerfile",
        ".dockerfile",
    }
)

EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        ".env",
        "node_modules",
        "dist",
        "build",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".eggs",
        "*.egg-info",
        "htmlcov",
        ".coverage",
    }
)

# Files excluded from scanning by design.  The scanner's own source file is
# excluded because it necessarily contains the banned pattern strings as keys
# in its BANNED_PATTERNS dictionary.
EXCLUDED_FILES: frozenset[str] = frozenset(
    {
        "tools/no_placeholders.py",
    }
)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Violation:
    path: str
    line_number: int
    marker: str
    line_content: str


@dataclass(frozen=True)
class AllowlistEntry:
    path: str
    line: int
    marker: str
    justification: str


# ---------------------------------------------------------------------------
# Allowlist loading
# ---------------------------------------------------------------------------


def load_allowlist(allowlist_path: Path) -> list[AllowlistEntry]:
    """Load and validate the allowlist JSON file."""
    if not allowlist_path.exists():
        return []

    try:
        raw = json.loads(allowlist_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: Cannot parse allowlist {allowlist_path}: {exc}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(raw, list):
        print(
            f"ERROR: Allowlist {allowlist_path} must be a JSON array.",
            file=sys.stderr,
        )
        sys.exit(2)

    entries: list[AllowlistEntry] = []
    for idx, item in enumerate(raw):
        for required_field in ("path", "line", "marker", "justification"):
            if required_field not in item:
                print(
                    f"ERROR: Allowlist entry #{idx} is missing required field "
                    f"'{required_field}'.",
                    file=sys.stderr,
                )
                sys.exit(2)
        if not item["justification"].strip():
            print(
                f"ERROR: Allowlist entry #{idx} has an empty justification.",
                file=sys.stderr,
            )
            sys.exit(2)
        entries.append(
            AllowlistEntry(
                path=item["path"],
                line=int(item["line"]),
                marker=item["marker"].upper(),
                justification=item["justification"],
            )
        )
    return entries


def build_allowlist_set(entries: list[AllowlistEntry]) -> frozenset[tuple[str, int, str]]:
    """Return a set of (relative_path, line_number, marker) triples for O(1) lookup."""
    return frozenset((e.path, e.line, e.marker.upper()) for e in entries)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def _is_excluded_dir(directory: Path) -> bool:
    """Return True if this directory should be skipped entirely."""
    return directory.name in EXCLUDED_DIRS or directory.name.endswith(".egg-info")


def iter_source_files(root: Path) -> Iterator[Path]:
    """Yield every source file under *root* that should be scanned."""
    for item in root.rglob("*"):
        if item.is_dir():
            continue
        # Skip anything inside an excluded directory at any depth.
        if any(_is_excluded_dir(parent) for parent in item.parents):
            continue
        # Skip explicitly excluded files (relative to root).
        try:
            rel = str(item.relative_to(root))
        except ValueError:
            continue
        if rel in EXCLUDED_FILES:
            continue
        suffix = item.suffix.lower()
        name = item.name
        # Match by suffix or exact filename (e.g. "Makefile", "Dockerfile").
        if suffix in SCANNED_EXTENSIONS or name in SCANNED_EXTENSIONS:
            yield item


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


def scan_file(
    filepath: Path,
    root: Path,
    allowlist_set: frozenset[tuple[str, int, str]],
) -> list[Violation]:
    """Scan a single file and return all violations not in the allowlist."""
    violations: list[Violation] = []
    rel_path = str(filepath.relative_to(root))

    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"WARNING: Cannot read {rel_path}: {exc}", file=sys.stderr)
        return violations

    for line_number, line in enumerate(text.splitlines(), start=1):
        for marker, pattern in BANNED_PATTERNS.items():
            if pattern.search(line):
                key = (rel_path, line_number, marker.upper())
                if key in allowlist_set:
                    continue
                violations.append(
                    Violation(
                        path=rel_path,
                        line_number=line_number,
                        marker=marker,
                        line_content=line.strip(),
                    )
                )
                # Report each banned marker once per line even if it appears
                # multiple times; break to avoid duplicate entries for the same
                # marker on the same line.
                break

    return violations


def run_scan(root: Path, allowlist_path: Path) -> list[Violation]:
    """Run the full scan and return all violations."""
    allowlist = load_allowlist(allowlist_path)
    allowlist_set = build_allowlist_set(allowlist)

    all_violations: list[Violation] = []
    for source_file in sorted(iter_source_files(root)):
        all_violations.extend(scan_file(source_file, root, allowlist_set))

    return all_violations


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_report(violations: list[Violation]) -> None:
    """Print a human-readable violation report."""
    if not violations:
        print("✓ Placeholder scan passed — no violations found.")
        return

    print(f"\n✗ Placeholder scan FAILED — {len(violations)} violation(s) found:\n")
    for v in violations:
        print(f"  {v.path}:{v.line_number}: [{v.marker}] {v.line_content}")

    print(
        "\nTo fix: remove the banned marker or, if the occurrence is intentional "
        "(e.g. a documentation example), add an entry to "
        "tools/no_placeholders_allowlist.json with a mandatory justification."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan source files for banned placeholder markers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to scan (default: current directory).",
    )
    parser.add_argument(
        "--allowlist",
        default="tools/no_placeholders_allowlist.json",
        help=(
            "Path to the allowlist JSON file relative to --root "
            "(default: tools/no_placeholders_allowlist.json)."
        ),
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"ERROR: Root directory '{root}' does not exist.", file=sys.stderr)
        return 2

    # Resolve allowlist path: if absolute use as-is, otherwise relative to root.
    allowlist_path = Path(args.allowlist)
    if not allowlist_path.is_absolute():
        allowlist_path = root / allowlist_path

    violations = run_scan(root, allowlist_path)
    print_report(violations)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
