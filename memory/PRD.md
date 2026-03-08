# PRD — MNN Repo Completion

## Original Problem Statement
help me complete this repo, making it fully operational and deployable

## Confirmed User Choices
- Scope: Fix runtime/build issues and missing features in parallel
- Must-have flow: Auth + main dashboard
- Deployment target: Vercel frontend + hosted backend
- Integrations: Mock/fallback behavior for non-critical dependencies

## Architecture Decisions
- Kept FastAPI backend as system-of-record and added operator auth on top
- Implemented signed bearer token auth without adding new backend dependencies
- Added dedicated dashboard APIs for operational metrics + infra status
- Added React + Vite frontend (separate deploy unit) optimized for Vercel static hosting
- Preserved existing pipeline/query APIs and test behavior
- Added optional infra checks (Postgres/Redis/MinIO/Keycloak) with graceful mock fallback
- Added supervisor-compatible backend entrypoint at `/app/backend/server.py` and frontend `start` script
- Enforced env/user-configured backend URL strategy in frontend (no hardcoded localhost fallback)

## Implemented
- Backend:
  - New auth token helpers (`auth_utils.py`)
  - New infra health aggregation (`infra_status.py`)
  - New endpoints: `/auth/login`, `/auth/me`, `/dashboard/overview`, `/infra/status`
  - Optional auth enforcement for `/query` via `API_AUTH_ENABLED`
  - Expanded configuration for auth + optional service URLs
- Frontend (`/app/frontend`):
  - React/Vite app with login + authenticated dashboard
  - Query runner, infra status cards, metrics cards, feedback chart
  - Backend URL configuration and session persistence
  - Vercel-ready SPA rewrite config (`frontend/vercel.json`)
- DevOps/CI:
  - CI expanded to include frontend build, auth/dashboard smoke checks, pip-audit, SBOM artifact
  - Added CodeQL workflow for Python/C++/JavaScript
  - Dockerfile updated to include new backend modules
  - Docker Compose expanded with optional Redis, MinIO, Keycloak services
- Quality:
  - Added auth/dashboard tests (`tests/test_auth_dashboard.py`)
  - Existing test suite remains passing
  - Recharts sizing warning resolved by explicit chart sizing based on container dimensions

## Prioritized Backlog
### P0
- Add production-grade secret management (remove default admin credentials)
- Add role-based auth (operator/admin) and token revocation/session invalidation
- Add real DB-backed user store and password hashing

### P1
- Add frontend code-splitting to reduce bundle size warning
- Add dashboard auto-refresh intervals and alert thresholds
- Add integration tests against real docker-compose services

### P2
- Add historical charts for latency/error trends
- Add per-service drill-down pages and logs explorer
- Add audit trail export for operator actions

## Next Tasks
1. Wire production env variables for backend auth secret and admin credentials
2. Deploy backend container and point `VITE_BACKEND_URL` to hosted API
3. Enable API auth for query endpoint in production (`API_AUTH_ENABLED=true`)
4. Run full CI in GitHub with supply-chain artifacts and CodeQL enabled

## Milestone Program (User-selected 1c)
- Milestone A (current): Hermetic build foundation, deterministic baseline checks, CI build-hermetic gate
- Milestone B (next): Cross-language RNG propagation and deterministic coordinate mapping baseline
- Milestone C: Formal lifecycle verification with Z3/pySMT in CI
- Milestone D: mmap corpus + replay/audit hash-chain execution
- Milestone E: Benchmarks, release hardening, and signed reproducible artifacts

## Milestone A Implemented
- Added `devops/nix/flake.nix` (Python 3.12 + C++ toolchain deterministic shell)
- Added `devops/docker/Dockerfile.hermetic` and `devops/locks/python-3.12-requirements.lock.txt`
- Added host variance + reproducible image scripts (`scripts/verify_host_variance.py`, `scripts/verify_docker_reproducibility.sh`)
- Added deterministic artifact generators (`tools/generate_architecture_artifacts.py`, `tools/reproducibility_check.py`)
- Added generated deterministic docs in `docs/deterministic/` (dependency graph, lifecycle model, reproducibility checks)
- Added CI `build-hermetic` job with Nix flake check + deterministic Docker rebuild verification + smoke checks
