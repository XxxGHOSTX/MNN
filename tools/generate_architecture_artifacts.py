"""Generate deterministic architecture and lifecycle artifacts."""

from __future__ import annotations

import json
from pathlib import Path


OUTPUT_DIR = Path("/app/docs/deterministic")


def write_dependency_graph() -> None:
    dot = """digraph thalos_prime {
  rankdir=LR;
  node [shape=box, style=rounded];

  api [label="api.py (control plane)"];
  mainpy [label="main.py (pipeline orchestrator)"];
  mnnpipe [label="mnn_pipeline/*"];
  mnncore [label="src/mnn_core.cpp"];
  detstatecpp [label="src/deterministic_state.cpp"];
  detctl [label="mnn/deterministic/control_plane.py"];
  detlife [label="mnn/deterministic/lifecycle.py"];
  detrng [label="mnn/deterministic/rng.py"];
  detaudit [label="mnn/deterministic/audit.py"];
  detbasile [label="mnn/deterministic/basile.py"];
  detformal [label="mnn/deterministic/formal.py"];
  middleware [label="middleware.py (bridge)"];
  metrics [label="metrics.py"];
  security [label="security.py"];
  feedback [label="feedback.py"];

  api -> mainpy;
  api -> mnnpipe;
  api -> metrics;
  api -> security;
  api -> feedback;
  api -> detctl;
  api -> detformal;
  api -> detbasile;
  mainpy -> mnnpipe;
  detctl -> detlife;
  detctl -> detaudit;
  detctl -> detrng;
  detctl -> detbasile;
  middleware -> mnncore;
  detrng -> detstatecpp;
}
"""
    (OUTPUT_DIR / "dependency_graph.dot").write_text(dot)


def write_lifecycle_model() -> None:
    model = {
        "lifecycle": [
            "initialize",
            "validate",
            "operate",
            "reconcile",
            "checkpoint",
            "terminate",
        ],
        "constraints": {
            "initialize_before_validate": True,
            "validate_before_operate": True,
            "reconcile_requires_hash_match": True,
            "checkpoint_requires_hash_match": True,
            "terminate_after_checkpoint": True,
            "deterministic_halt_on_violation": True,
        },
        "determinism_controls": {
            "seed_propagation": "required",
            "prng_state_synchronization": "required",
            "cross_language_entropy_control": "required",
            "python_hash_seed": "0",
        },
        "nexus_v3_modules": {
            "nucleus": "deterministic ingestion + validation",
            "spine": "hash-chained JSONL provenance log",
            "mitochondria": "execution governor + deterministic halt",
        },
    }
    (OUTPUT_DIR / "lifecycle_verification_model.json").write_text(json.dumps(model, indent=2, sort_keys=True))


def write_repro_checks() -> None:
    md = """# Reproducibility Validation Checks

1. Enforce `DETERMINISTIC_MODE=true`.
2. Enforce `PYTHONHASHSEED=0`.
3. Run the same query and seed twice; compare SHA256 of serialized output.
4. Build hermetic Dockerfile twice; image IDs must match.
5. Validate lifecycle ordering constraints before runtime execution.
6. Validate Python/C++ SplitMix64 descriptor parity.
7. Replay hash-chained JSONL logs and verify final digest.
8. Generate Basile coordinate volumes and assert bit-for-bit hash identity across runs.
"""
    (OUTPUT_DIR / "reproducibility_checks.md").write_text(md)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_dependency_graph()
    write_lifecycle_model()
    write_repro_checks()
    print(f"Generated artifacts in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
