# Reproducibility Validation Checks

1. Enforce `DETERMINISTIC_MODE=true`.
2. Enforce `PYTHONHASHSEED=0`.
3. Run the same query and seed twice; compare SHA256 of serialized output.
4. Build hermetic Dockerfile twice; image IDs must match.
5. Validate lifecycle ordering constraints before runtime execution.
