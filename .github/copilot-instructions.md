# MNN — Copilot / Agent Instructions (Enforcement-First Profile)

> **Enforcement level: STRICT.**  Every rule in this file is a hard gate.
> Flexible or non-blocking interpretations are explicitly rejected.

---

## Absolute prohibitions — instant failure

The following markers are **never** acceptable in committed code, tests,
documentation, or configuration files:

| Marker | Why banned |
|--------|-----------|
| `TODO` | Signals incomplete work — ship complete work only |
| `FIXME` | Signals a known defect — fix it before merging |
| `STUB` | Placeholder implementation — replace with real code |
| `MOCK` (outside test doubles that are properly named and typed) | Ambiguous intent — use explicit test fixtures |
| `PLACEHOLDER` | Self-explanatory |
| `TBD` | Deferred decision — decide now |
| `HACK` | Acknowledges bad code — write good code |
| `XXX` (as a code-comment marker) | Informal deferrals are banned |

The automated marker scanner (`tools/no_placeholders.py`) is run on
every PR and push to `main`.  A single match is a merge-blocking failure.

To suppress a **genuinely intentional** occurrence (e.g., a documentation
example that must literally contain the word TODO), add the file path and line
to `tools/no_placeholders_allowlist.json` with a mandatory justification field.
Allowlist entries are reviewed as part of code review.

---

## Determinism requirements

All randomness in the codebase must be:

1. **Seeded explicitly** — never call `random.random()`, `numpy.random.rand()`,
   or any RNG without first setting a named, logged seed.
2. **Seed logged** — emit the seed value at `INFO` level before any stochastic
   operation so failures are reproducible.
3. **Tested for determinism** — every stochastic component must have at least
   one test that runs the operation twice with the same seed and asserts
   identical output.
4. **Reproducibility CI gate** — the `verify-lifecycle` and
   `cross-language-rng-check` jobs enforce Python/C++ RNG descriptor parity.

Reference implementation: `mnn/core/seed_registry.py`.

---

## Production-quality rules

- **No prototype or partial implementations.** Every function/class merged to
  `main` must be complete, tested, and documented.
- **Explicit error handling.** Bare `except Exception: pass` and silent
  fallbacks are banned. Raise or log with full context, then re-raise or return
  an explicit error type.
- **No silent data loss.** If an operation can fail, the caller must handle the
  failure path — no swallowing exceptions and returning empty results without
  logging.
- **Type annotations required.** All public function signatures must carry
  Python type hints. Run `make lint` (which includes `py_compile` validation)
  before every push.
- **No dead code.** Commented-out code blocks are treated the same as TODO
  comments — remove them or track the need via a GitHub Issue.

---

## Repository layout

```
.github/
  copilot-instructions.md    ← this file
  pull_request_template.md   ← enforced PR checklist
  workflows/
    ci.yml                   ← full CI pipeline (lint → test → marker-scan → verify → docker-smoke → deploy)
    codeql.yml               ← security scanning
api.py                       ← FastAPI v2 entrypoint (versioned /v2/ prefix)
auth_utils.py                ← JWT authentication utilities
config.py                    ← environment-driven configuration
logging_config.py            ← structured logging (use datetime.now(timezone.utc))
metrics.py                   ← production metrics collector
middleware.py                ← PostgreSQL bridge (requires THALOS_DB_DSN)
security.py                  ← security helpers
feedback.py                  ← feedback recording
main.py                      ← application entry point
mnn/                         ← core library
  babel_siphon.py            ← SMT-Arbiter deterministic generation pipeline
  core/seed_registry.py      ← canonical seeded-RNG registry
  solver/smt_solver.py       ← Z3 SMT validation
  ucs/kernel.py              ← Library-of-Sense integration
  control/plane.py           ← control plane
  guard/logic_guard.py       ← logical guard
  verification/verifier.py   ← formal verifier
  search/neuro_symbolic.py   ← neuro-symbolic search
  codegen/virtuoso.py        ← code generation
  tests/                     ← mnn-specific unit tests
src/                         ← legacy Python modules + C++ core
  mnn_core.cpp               ← C++17 tensor math (broadcast, matmul, geo-embed)
include/mnn_core.hpp         ← C++ header
tests/                       ← top-level pytest suite (run with `make test`)
tools/                       ← developer and CI utilities
  no_placeholders.py         ← marker scanner (run via `make marker-scan`)
  no_placeholders_allowlist.json ← allowlist for intentional strings
  run_ci.sh                  ← local CI runner (mirrors GitHub Actions gates)
  verify.py                  ← verification agent
  verify_lifecycle_formal.py ← formal lifecycle invariant checks
sql/                         ← DDL for relational buffer schema
```

---

## Running checks locally

```bash
# Install dependencies (Python 3.12 required)
pip install -r requirements.txt

# Lint (py_compile validation)
make lint

# Unit tests
make test

# Marker scan (must pass before every push)
python tools/no_placeholders.py

# Full local CI mirror (runs all gates in order)
bash tools/run_ci.sh

# C++ core compile check
g++ -std=c++17 -Iinclude -c src/mnn_core.cpp

# Deterministic benchmark + lifecycle verification
make verify-lifecycle
make cross-language-rng-check
make benchmark-deterministic
```

---

## Adding a new module

1. Create the module under the appropriate package (`mnn/`, `src/`, `tools/`).
2. Add full type annotations to every public function/class.
3. Write tests in `tests/` (or `mnn/tests/` for mnn-specific tests).
4. Ensure tests cover both the happy path and all explicit error paths.
5. If the module uses randomness, register seeds via `mnn/core/seed_registry.py`
   and add a determinism test.
6. Run `bash tools/run_ci.sh` locally — all gates must pass before opening a PR.
7. Fill in `.github/pull_request_template.md` completely — no fields may be
   left blank.

---

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `THALOS_DB_DSN` | For DB operations | PostgreSQL connection string |
| `THALOS_DB_CONNECT_TIMEOUT` | Optional | Connect timeout in seconds |
| `THALOS_HARDWARE_ID` | Optional | Override hardware-bound encryption key |

---

## Security notes

- Never commit secrets, credentials, or private keys.
- All JWT tokens are validated via `auth_utils.py` — do not bypass.
- Dependency audits run via `pip-audit` in the `supply-chain` CI job.
- SBOM is generated on every push to `main`.
- CodeQL scans run on every PR via `.github/workflows/codeql.yml`.
