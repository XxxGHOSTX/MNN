"""Cross-language deterministic descriptor parity tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_cross_language_rng_descriptor_parity():
    proc = subprocess.run(
        ["python", "tools/cross_language_rng_check.py"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
