# Milestone A Revert Playbook

Use this when reproducibility assets block delivery.

## Scope to revert

- `devops/nix/`
- `devops/docker/Dockerfile.hermetic`
- `devops/locks/python-3.12-requirements.lock.txt`
- `scripts/verify_docker_reproducibility.sh`
- `scripts/verify_host_variance.py`
- CI `build-hermetic` job changes

## Revert sequence

1. Disable `build-hermetic` job in `.github/workflows/ci.yml`.
2. Remove deterministic Docker reproducibility script calls from CI.
3. Keep runtime API and existing smoke tests untouched.
4. Validate baseline with:
   - `make lint`
   - `pytest -q`
   - existing docker smoke job

## Safety checks

- Confirm `/health` and `/api/version` still return 200.
- Confirm frontend build still succeeds.
- Keep `DETERMINISTIC_MODE` env variable accepted by config to avoid runtime env drift.
