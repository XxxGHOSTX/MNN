"""Cross-language deterministic descriptor parity tests."""

from __future__ import annotations

import subprocess


def test_cross_language_rng_descriptor_parity():
    proc = subprocess.run(
        ["python", "tools/cross_language_rng_check.py"],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
