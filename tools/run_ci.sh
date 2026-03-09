#!/usr/bin/env bash
# tools/run_ci.sh — Local CI runner
#
# Mirrors the GitHub Actions CI gates in order so you can validate your
# changes locally before pushing.  All steps run with set -euo pipefail;
# the script aborts on the first failure and prints a clear error.
#
# Usage:
#   bash tools/run_ci.sh              # Run all gates
#   bash tools/run_ci.sh --fast       # Skip docker-smoke and C++ compile
#
# Requirements:
#   - Python 3.12+ on PATH
#   - pip dependencies installed (will be installed automatically)
#   - g++ available for C++ compile step (skipped with --fast)
#   - Docker available for docker-smoke step (skipped with --fast)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FAST=false
HEALTH_CHECK_RETRIES=30
for arg in "$@"; do
  case "$arg" in
    --fast) FAST=true ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_step() {
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "  $1"
  echo "═══════════════════════════════════════════════════════════════"
}

_ok() {
  echo "  ✓ $1"
}

_skip() {
  echo "  ⊘ $1 (skipped — use without --fast to enable)"
}

# ---------------------------------------------------------------------------
# 1. Install dependencies
# ---------------------------------------------------------------------------

_step "1/6  Install dependencies"
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
_ok "Dependencies installed"

# ---------------------------------------------------------------------------
# 2. Lint
# ---------------------------------------------------------------------------

_step "2/6  Lint"
make lint
_ok "Lint passed"

# ---------------------------------------------------------------------------
# 3. Marker scan
# ---------------------------------------------------------------------------

_step "3/6  Marker scan"
python tools/no_placeholders.py --root . --allowlist tools/no_placeholders_allowlist.json
_ok "Marker scan passed"

# ---------------------------------------------------------------------------
# 4. Tests
# ---------------------------------------------------------------------------

_step "4/6  Tests"
make test
_ok "Tests passed"

# ---------------------------------------------------------------------------
# 5. Verification agent + C++ core compile
# ---------------------------------------------------------------------------

_step "5/6  Verify"
python -m tools.verify
_ok "Verification agent passed"

if $FAST; then
  _skip "C++ core compile"
else
  if command -v g++ &>/dev/null; then
    g++ -std=c++17 -Iinclude -c src/mnn_core.cpp -o /tmp/mnn_core_local.o
    _ok "C++ core compiled"
  else
    echo "  ⚠ g++ not found — skipping C++ compile (install g++ to enable)"
  fi
fi

# ---------------------------------------------------------------------------
# 6. Docker smoke test
# ---------------------------------------------------------------------------

_step "6/6  Docker smoke test"

if $FAST; then
  _skip "Docker smoke test"
elif ! command -v docker &>/dev/null; then
  echo "  ⚠ docker not found — skipping smoke test"
else
  echo "  Building Docker image..."
  docker build -t mnn-pipeline:local . --quiet

  echo "  Starting container..."
  docker run -d --name mnn-local-smoke -p 18000:8000 mnn-pipeline:local

  cleanup() {
    docker stop mnn-local-smoke &>/dev/null || true
    docker rm mnn-local-smoke &>/dev/null || true
  }
  trap cleanup EXIT

  echo "  Waiting for API to become healthy..."
  for i in $(seq 1 "${HEALTH_CHECK_RETRIES}"); do
    if curl -sf http://localhost:18000/health &>/dev/null; then
      break
    fi
    sleep 2
  done

  response=$(curl -sf http://localhost:18000/health)
  echo "$response" | grep -q "healthy"
  _ok "Health endpoint OK"

  docker stop mnn-local-smoke &>/dev/null
  docker rm mnn-local-smoke &>/dev/null
  trap - EXIT
  _ok "Docker smoke test passed"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo " All CI gates passed. Ready to push."
echo "═══════════════════════════════════════════════════════════════"
echo ""
