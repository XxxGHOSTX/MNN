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
  middleware [label="middleware.py (bridge)"];
  metrics [label="metrics.py"];
  security [label="security.py"];
  feedback [label="feedback.py"];

  api -> mainpy;
  api -> mnnpipe;
  api -> metrics;
  api -> security;
  api -> feedback;
  mainpy -> mnnpipe;
  middleware -> mnncore;
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
        },
        "determinism_controls": {
            "seed_propagation": "required",
            "prng_state_synchronization": "required",
            "cross_language_entropy_control": "required",
            "python_hash_seed": "0",
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
