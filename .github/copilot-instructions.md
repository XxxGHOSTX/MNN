# Copilot onboarding for MNN

Repository overview and quick pointers for agents seeing this codebase for the first time.

## Layout
- `src/`: Python implementation.
  - `permutation/engine.py`: permutation generator and refinement stages.
  - `mind/llm_handler.py`: geometric embeddings, semantic sieve, and text generation.
  - `encryption/weight_encryptor.py`: numpy-based XOR encryptor with rotation.
  - `buffer/relational_buffer.py`: in-memory/mock PostgreSQL buffer helpers and schema strings.
  - `thalos/linear_algebra.py`: matrix helpers used by the examples.
- `include/mnn_core.hpp` + `src/mnn_core.cpp`: C++17 tensor math core (broadcasting, matmul, geometric embedding).
- `middleware.py`: real PostgreSQL bridge using `psycopg2`; requires `THALOS_DB_DSN` (and optional `THALOS_DB_CONNECT_TIMEOUT`) to be set.
- `sql/relational_buffer_schema.sql`: DDL for the relational buffer tables.
- `tests/`: `unittest` modules; they `sys.path.insert` the repo `src` directory and expect to run from repo root.

## Setup
- Python: `pip install -r requirements.txt` (numpy, psycopg2-binary, cryptography). Default user install is fine in the sandbox.
- For middleware usage, export `THALOS_DB_DSN=postgresql://user:pass@host:port/db` before interacting with the real database. Optional `THALOS_DB_CONNECT_TIMEOUT` controls connect timeout seconds.
- Hardware-bound encryption can be overridden with `THALOS_HARDWARE_ID` (used by `weight_encryptor.py`).

## Build & test
- Python tests: run from repo root
  - `python -m unittest discover tests`
  - Targeted: `python -m unittest tests.test_thalos` (or other modules)
- C++ sanity compile for the core: `g++ -std=c++17 -Iinclude -c src/mnn_core.cpp`
- Tests are pure Python/memory-bound; `middleware.py` is not exercised by the suite.

## Known issues & workarounds
- Initial test run failed with `ModuleNotFoundError: No module named 'numpy'` when dependencies were missing; fixed by `pip install -r requirements.txt`, after which `python -m unittest discover tests` passed (54 tests).
- Running middleware without `THALOS_DB_DSN` raises `ValueError`; set the env var when using the bridge or avoid invoking those paths in tests.

## Tips for effective changes
- Keep imports relative to the repo root (tests rely on `sys.path` injection). Run commands from `/home/runner/work/MNN/MNN`.
- Prefer updating Python modules under `src/`; C++ core is standalone and compiled separately for checks.
- Avoid touching `.github/agents` if present.
- When modifying encryption, respect existing hardware-binding (checksums, hardware hash) to avoid breaking decryption.
