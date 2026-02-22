"""
MNN Repository Verification Agent

Validates the repository state deterministically and emits a JSON report.

Steps performed (in order):
  1. Check required files exist
  2. Compile all Python sources (py_compile)
  3. Run the canonical test suite (pytest)
  4. Compile C++ core sanity check
  5. Emit deterministic JSON report to stdout and verification_report.json

Exit code 0 on success, 1 on any failure.

Usage:
    python -m tools.verify
    python tools/verify.py
"""

import json
import os
import subprocess
import sys
import py_compile
from datetime import datetime, timezone
from pathlib import Path

# Repository root is two levels up from this file
REPO_ROOT = Path(__file__).resolve().parent.parent

# Required files that must exist for the repository to be operational
REQUIRED_FILES = [
    "requirements.txt",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    ".env.example",
    "api.py",
    "main.py",
    "config.py",
    "logging_config.py",
    "security.py",
    "metrics.py",
    "feedback.py",
    "middleware.py",
    "include/mnn_core.hpp",
    "src/mnn_core.cpp",
    "mnn/control/plane.py",
    "mnn/verification/verifier.py",
    "sql/relational_buffer_schema.sql",
    "tests/__init__.py",
]


def _ts() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def check_required_files() -> dict:
    """Verify all required files are present."""
    missing = []
    for rel_path in sorted(REQUIRED_FILES):
        if not (REPO_ROOT / rel_path).exists():
            missing.append(rel_path)
    return {
        "step": "required_files",
        "passed": len(missing) == 0,
        "missing": missing,
    }


def compile_python_sources() -> dict:
    """Compile all Python sources with py_compile to catch syntax errors."""
    errors = []
    compiled = 0
    py_files = sorted(REPO_ROOT.rglob("*.py"))
    for f in py_files:
        # Skip hidden dirs and __pycache__
        parts = f.relative_to(REPO_ROOT).parts
        if any(p.startswith(".") or p == "__pycache__" for p in parts):
            continue
        compiled += 1
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append({"file": str(f.relative_to(REPO_ROOT)), "error": str(exc)})
    return {
        "step": "python_compile",
        "passed": len(errors) == 0,
        "files_checked": compiled,
        "errors": errors,
    }


def run_tests() -> dict:
    """Run the canonical test suite with pytest."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--tb=short"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    output_lines = (result.stdout + result.stderr).splitlines()
    # Extract the pytest summary line (contains " passed" with leading digit/count)
    summary = next(
        (l for l in reversed(result.stdout.splitlines())
         if ("passed" in l or "failed" in l) and "in " in l),
        "",
    )
    return {
        "step": "pytest",
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "summary": summary,
        "output_tail": output_lines[-10:] if len(output_lines) > 10 else output_lines,
    }


def compile_cpp_core() -> dict:
    """Sanity-compile the C++ core to catch compilation errors."""
    obj_file = "/tmp/mnn_core_verify.o"
    result = subprocess.run(
        [
            "g++",
            "-std=c++17",
            f"-I{REPO_ROOT / 'include'}",
            "-c",
            str(REPO_ROOT / "src" / "mnn_core.cpp"),
            "-o",
            obj_file,
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    # Clean up object file
    try:
        os.unlink(obj_file)
    except FileNotFoundError:
        pass
    return {
        "step": "cpp_compile",
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "stderr": result.stderr.strip() if result.returncode != 0 else "",
    }


def main() -> int:
    """Run all verification steps and emit a deterministic JSON report."""
    report = {
        "agent": "mnn-verify",
        "version": "1.0.0",
        "timestamp": _ts(),
        "repo_root": str(REPO_ROOT),
        "steps": [],
    }

    all_passed = True

    # Steps are executed in deterministic order
    steps = [
        check_required_files,
        compile_python_sources,
        run_tests,
        compile_cpp_core,
    ]

    for step_fn in steps:
        step_result = step_fn()
        report["steps"].append(step_result)
        if not step_result["passed"]:
            all_passed = False

    report["overall"] = "PASSED" if all_passed else "FAILED"

    # Emit JSON report
    report_json = json.dumps(report, indent=2, sort_keys=False)
    print(report_json)

    # Write report file
    report_path = REPO_ROOT / "verification_report.json"
    report_path.write_text(report_json + "\n", encoding="utf-8")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
