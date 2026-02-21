"""
MNN Automation Agent – core orchestration.

Validation order is fixed and deterministic:
  1. discovery   – enumerate repository components
  2. deps        – verify required Python packages importable
  3. envvars     – detect broken env-var assumptions
  4. lint        – compile-check every .py file
  5. test        – run unittest suite
  6. cpp         – compile mnn_core.cpp with g++
  7. imports     – spot-check critical cross-module imports

Each step runs independently; failures are collected and the agent
returns a non-zero exit code when any check fails (fail-fast can be
toggled via ``fail_fast=True``).  Full run state is written to
``agent_run.log`` in the repository root.
"""

from __future__ import annotations

import datetime
import enum
import importlib
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence


# ---------------------------------------------------------------------------
# Public status enum
# ---------------------------------------------------------------------------

class CheckStatus(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    detail: str = ""


@dataclass
class AgentResult:
    checks: List[CheckResult] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    repo_root: str = ""

    # ---- helpers -----------------------------------------------------------

    def passed(self) -> bool:
        return all(c.status in (CheckStatus.PASS, CheckStatus.SKIP) for c in self.checks)

    def summary(self) -> str:
        lines: List[str] = [
            f"MNN Agent run at {self.started_at}",
            f"Repository root: {self.repo_root}",
            "",
        ]
        for c in self.checks:
            icon = "✓" if c.status == CheckStatus.PASS else ("↷" if c.status == CheckStatus.SKIP else "✗")
            lines.append(f"  {icon} [{c.status.value.upper():4}] {c.name}")
            if c.detail:
                for line in c.detail.splitlines():
                    lines.append(f"           {line}")
        lines.append("")
        overall = "PASS" if self.passed() else "FAIL"
        lines.append(f"Overall: {overall}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "repo_root": self.repo_root,
            "passed": self.passed(),
            "checks": [
                {"name": c.name, "status": c.status.value, "detail": c.detail}
                for c in self.checks
            ],
        }


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class Agent:
    """Deterministic MNN repository maintenance agent."""

    # Ordered list of check names; execution order is fixed.
    CHECK_ORDER: Sequence[str] = (
        "discovery",
        "deps",
        "envvars",
        "lint",
        "test",
        "cpp",
        "imports",
    )

    # Required Python packages (importable names → pip names)
    REQUIRED_PACKAGES: Dict[str, str] = {
        "numpy": "numpy",
        "pydantic": "pydantic",
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "psycopg2": "psycopg2-binary",
        "cryptography": "cryptography",
        "httpx": "httpx",
        "z3": "z3-solver",
    }

    # Optional: env vars to check for definition (not required for tests)
    OPTIONAL_ENV_VARS: Sequence[str] = ("THALOS_DB_DSN", "THALOS_DB_CONNECT_TIMEOUT", "THALOS_HARDWARE_ID")

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        checks: Optional[Sequence[str]] = None,
        fail_fast: bool = False,
        log_file: Optional[Path] = None,
    ) -> None:
        self.repo_root: Path = (
            repo_root if repo_root is not None else Path(__file__).resolve().parents[2]
        )
        self.checks: Sequence[str] = checks if checks is not None else self.CHECK_ORDER
        self.fail_fast = fail_fast
        self.log_file: Path = (
            log_file if log_file is not None else self.repo_root / "agent_run.log"
        )

    # ---- public entry point -----------------------------------------------

    def run(self) -> AgentResult:
        result = AgentResult(
            started_at=_now(),
            repo_root=str(self.repo_root),
        )

        for name in self.CHECK_ORDER:
            if name not in self.checks:
                result.checks.append(CheckResult(name=name, status=CheckStatus.SKIP, detail="not selected"))
                continue

            method = getattr(self, f"_check_{name}", None)
            if method is None:
                result.checks.append(CheckResult(name=name, status=CheckStatus.SKIP, detail="no implementation"))
                continue

            check = method()
            result.checks.append(check)

            if self.fail_fast and check.status == CheckStatus.FAIL:
                # Record remaining as skipped
                remaining = [n for n in self.CHECK_ORDER if n not in {c.name for c in result.checks}]
                for remaining_name in remaining:
                    result.checks.append(
                        CheckResult(name=remaining_name, status=CheckStatus.SKIP, detail="skipped due to fail-fast")
                    )
                break

        result.finished_at = _now()
        self._persist(result)
        return result

    # ---- individual checks ------------------------------------------------

    def _check_discovery(self) -> CheckResult:
        """Enumerate repository components and verify expected structure."""
        expected_dirs = ["mnn", "tests", "src", "include", "mnn_pipeline", "sql", "tools"]
        expected_files = [
            "requirements.txt",
            "Makefile",
            "Dockerfile",
            "src/mnn_core.cpp",
            "include/mnn_core.hpp",
            "sql/relational_buffer_schema.sql",
        ]
        missing: List[str] = []

        for d in expected_dirs:
            if not (self.repo_root / d).is_dir():
                missing.append(f"directory: {d}/")

        for f in expected_files:
            if not (self.repo_root / f).is_file():
                missing.append(f"file: {f}")

        py_files = list(self.repo_root.rglob("*.py"))
        py_count = len([p for p in py_files if ".git" not in str(p)])

        detail = f"Found {py_count} Python source files."
        if missing:
            detail += "\nMissing components:\n" + "\n".join(f"  - {m}" for m in missing)
            return CheckResult(name="discovery", status=CheckStatus.FAIL, detail=detail)

        return CheckResult(name="discovery", status=CheckStatus.PASS, detail=detail)

    def _check_deps(self) -> CheckResult:
        """Verify all required Python packages can be imported."""
        failed: List[str] = []
        for import_name, pip_name in self.REQUIRED_PACKAGES.items():
            try:
                importlib.import_module(import_name)
            except ImportError:
                failed.append(f"{import_name} (pip install {pip_name})")

        if failed:
            detail = "Missing packages:\n" + "\n".join(f"  - {p}" for p in failed)
            return CheckResult(name="deps", status=CheckStatus.FAIL, detail=detail)

        return CheckResult(name="deps", status=CheckStatus.PASS, detail=f"All {len(self.REQUIRED_PACKAGES)} required packages available.")

    def _check_envvars(self) -> CheckResult:
        """Detect broken environment variable assumptions in source files."""
        issues: List[str] = []

        # THALOS_DB_CONNECT_TIMEOUT must parse as int if set
        raw = os.getenv("THALOS_DB_CONNECT_TIMEOUT", "10")
        try:
            int(raw)
        except ValueError:
            issues.append(f"THALOS_DB_CONNECT_TIMEOUT={raw!r} is not a valid integer")

        # Warn (not fail) about unset optional vars
        unset = [v for v in self.OPTIONAL_ENV_VARS if not os.getenv(v)]
        detail_parts: List[str] = []
        if issues:
            detail_parts.append("Errors:\n" + "\n".join(f"  - {i}" for i in issues))
        if unset:
            detail_parts.append("Unset optional vars (tests do not require them):\n" + "\n".join(f"  - {v}" for v in unset))

        if issues:
            return CheckResult(name="envvars", status=CheckStatus.FAIL, detail="\n".join(detail_parts))

        detail = "\n".join(detail_parts) if detail_parts else "Environment variable assumptions satisfied."
        return CheckResult(name="envvars", status=CheckStatus.PASS, detail=detail)

    def _check_lint(self) -> CheckResult:
        """Compile-check all .py files in the repository."""
        failures: List[str] = []
        py_files = sorted(
            p for p in self.repo_root.rglob("*.py")
            if ".git" not in str(p)
        )
        for path in py_files:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(path)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                failures.append(f"{path.relative_to(self.repo_root)}: {result.stderr.strip()}")

        if failures:
            detail = f"{len(failures)} file(s) failed compile check:\n" + "\n".join(f"  {f}" for f in failures)
            return CheckResult(name="lint", status=CheckStatus.FAIL, detail=detail)

        return CheckResult(name="lint", status=CheckStatus.PASS, detail=f"All {len(py_files)} Python files pass compile check.")

    def _check_test(self) -> CheckResult:
        """Run the unittest discovery suite under tests/."""
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "tests"],
            capture_output=True,
            text=True,
            cwd=str(self.repo_root),
        )
        output = (result.stdout + result.stderr).strip()
        if result.returncode != 0:
            detail = textwrap.shorten(output, width=2000, placeholder="... (truncated)")
            return CheckResult(name="test", status=CheckStatus.FAIL, detail=detail)

        # Extract summary line (last non-empty line, e.g. "Ran 310 tests in 1.3s")
        summary = next((l for l in reversed(output.splitlines()) if l.strip()), "")
        return CheckResult(name="test", status=CheckStatus.PASS, detail=summary)

    def _check_cpp(self) -> CheckResult:
        """Compile src/mnn_core.cpp with g++ -std=c++17."""
        cpp_src = self.repo_root / "src" / "mnn_core.cpp"
        include_dir = self.repo_root / "include"

        if not cpp_src.is_file():
            return CheckResult(name="cpp", status=CheckStatus.SKIP, detail="src/mnn_core.cpp not found")

        # Check g++ availability
        which = subprocess.run(["which", "g++"], capture_output=True, text=True)
        if which.returncode != 0:
            return CheckResult(name="cpp", status=CheckStatus.SKIP, detail="g++ not found in PATH")

        with tempfile.TemporaryDirectory() as tmpdir:
            obj_file = Path(tmpdir) / "mnn_core.o"
            result = subprocess.run(
                ["g++", "-std=c++17", f"-I{include_dir}", "-c", str(cpp_src), "-o", str(obj_file)],
                capture_output=True,
                text=True,
            )

        if result.returncode != 0:
            return CheckResult(name="cpp", status=CheckStatus.FAIL, detail=result.stderr.strip())

        return CheckResult(name="cpp", status=CheckStatus.PASS, detail="src/mnn_core.cpp compiled successfully with -std=c++17.")

    def _check_imports(self) -> CheckResult:
        """Spot-check critical cross-module imports."""
        critical_imports = [
            ("mnn.pipeline", "run_pipeline"),
            ("mnn.core.seed_registry", "SeedRegistry"),
            ("mnn.ir.models", "ConstraintSchema"),
            ("mnn.solver.smt_solver", "SMTSolver"),
        ]
        failures: List[str] = []

        for module_path, attr in critical_imports:
            try:
                mod = importlib.import_module(module_path)
                if not hasattr(mod, attr):
                    failures.append(f"{module_path}.{attr}: attribute not found")
            except Exception as exc:
                failures.append(f"{module_path}: {exc}")

        if failures:
            detail = "Import failures:\n" + "\n".join(f"  - {f}" for f in failures)
            return CheckResult(name="imports", status=CheckStatus.FAIL, detail=detail)

        return CheckResult(name="imports", status=CheckStatus.PASS, detail=f"All {len(critical_imports)} critical imports verified.")

    # ---- persistence -------------------------------------------------------

    def _persist(self, result: AgentResult) -> None:
        """Write full run state as JSON to log_file."""
        try:
            self.log_file.write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass  # non-fatal; best effort


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.datetime.now(tz=datetime.timezone.utc).isoformat(timespec="seconds")
