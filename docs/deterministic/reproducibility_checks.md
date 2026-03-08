# Reproducibility Validation Checks

1. Enforce `DETERMINISTIC_MODE=true`.
2. Enforce `PYTHONHASHSEED=0`.
3. Run the same query and seed twice; compare SHA256 of serialized output.
4. Build hermetic Dockerfile twice; image IDs must match.
5. Validate lifecycle ordering constraints before runtime execution.
6. Validate Python/C++ SplitMix64 descriptor parity.
7. Replay hash-chained JSONL logs and verify final digest.
8. Generate Basile coordinate volumes and assert bit-for-bit hash identity across runs.
