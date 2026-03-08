# Deterministic DevOps Foundation (Milestone A)

This directory contains reproducibility-first infrastructure assets for Thalos Prime / MNN.

## Contents

- `nix/flake.nix` — hermetic developer/runtime environment definition (Python 3.12 + C++ toolchain)
- `docker/Dockerfile.hermetic` — deterministic container build variant
- `locks/python-3.12-requirements.lock.txt` — pinned Python dependency lock snapshot
- `revert/milestone_a_revert.md` — rollback playbook for this milestone

## Quickstart

### 1) Host variance check

```bash
python scripts/verify_host_variance.py
```

### 2) Nix shell (when Nix is available)

```bash
nix develop ./devops/nix
```

### 3) Deterministic docker reproducibility check

```bash
bash scripts/verify_docker_reproducibility.sh
```

### 4) Determinism smoke checks

```bash
python tools/reproducibility_check.py --query "deterministic systems"
python tools/generate_architecture_artifacts.py
python tools/verify_lifecycle_formal.py
python tools/cross_language_rng_check.py
```

## Build determinism policies

1. `DETERMINISTIC_MODE=true` by default.
2. `PYTHONHASHSEED=0` is enforced in hermetic images.
3. C++ compile checks use deterministic flags (`-fno-fast-math`, `-ffp-contract=off`).
4. Docker reproducibility must pass (same image ID over consecutive builds in CI).
5. Lifecycle mapping artifacts are generated deterministically into `docs/deterministic/`.
