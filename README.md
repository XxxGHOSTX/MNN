# THALOS: Matrix Neural Network (MNN)

> A deterministic, constraint-driven knowledge engine that transforms the infinite permutation space of [libraryofbabel.info](https://libraryofbabel.info) into a practical, queryable system returning only validated, relevant results.

---

## Table of Contents

1. [What is MNN?](#what-is-mnn)
2. [How it Works](#how-it-works)
3. [Repository Layout](#repository-layout)
4. [Quick Start](#quick-start)
5. [Usage](#usage)
   - [Command-Line Interface](#command-line-interface)
   - [REST API](#rest-api)
   - [Babel Siphon Pipeline](#babel-siphon-pipeline)
   - [Operator Dashboard](#operator-dashboard)
6. [Configuration](#configuration)
7. [Architecture](#architecture)
8. [Development](#development)
9. [Docker & Deployment](#docker--deployment)
10. [CI/CD](#cicd)
11. [License](#license)

---

## What is MNN?

**THALOS** (The Heuristic Algorithm for Lattice-Optimized Synthesis) is the engine powering the **Matrix Neural Network (MNN)** system. It is a research-grade, production-ready knowledge platform with five interlocking layers:

| Layer | What it does |
|---|---|
| **Permutation Engine** | Generates and refines sequences from a 29-character set (a–z, space, comma, period), replicating the Library of Babel's infinite combinatorial space |
| **MNN Pipeline** | 7-stage deterministic query pipeline: normalize → constrain → map indices → generate → filter → score → output |
| **Babel Siphon** | SMT-Arbiter pipeline that validates all output against formal Z3 constraints before emission |
| **Deterministic Runtime** | Hash-chained JSONL audit log, lifecycle state-machine, cross-language RNG parity, and replay validation |
| **Operator API & Dashboard** | FastAPI REST backend + React/Vite frontend for querying the engine and inspecting infrastructure |

The core insight: instead of scanning an infinite permutation space (99.999% noise), MNN **calculates exactly where relevant content lives** and jumps there — same query, same result, every time.

---

## How it Works

### 7-Stage Pipeline

```
Query Input
    │
    ▼
1. Query Normalization      – uppercase, strip non-alphanumeric, collapse whitespace
    │
    ▼
2. Constraint Generation    – derive min/max length bounds from the normalized pattern
    │
    ▼
3. Index Mapping            – deterministic function: indices = [0, step, 2·step … 999·step]
    │                         where step = len(pattern)  → 1000 candidate positions
    ▼
4. Sequence Generation      – produce "book" text at each mapped index
    │
    ▼
5. Analysis / Filtering     – validate pattern presence, length bounds, uniqueness
    │
    ▼
6. Scoring / Ranking        – center-weighted score: 1 / (1 + |center − pattern_pos|)
    │
    ▼
7. Output                   – top-N results returned (10 for CLI, 5 for API)
```

### Key Concepts

**Deterministic Index Mapping** — The same query always maps to the same 1000 candidate positions. No randomness, no scanning. This is what makes caching, replay, and auditability possible.

**Semantic Sieve** — Filters out 99.999% of generated noise, retaining only sequences that align with known linguistic structures.

**Geometric Character Embeddings** — Each of the 29 characters is mapped to a vertex in a high-dimensional manifold instead of using BPE tokenization. Meaning emerges from relational distances between vertices.

**SMT Validation (Babel Siphon)** — Every output candidate is checked against formal constraints (length, token containment, character set, code invariants) by the Z3 SMT solver before being returned. Failed candidates are automatically repaired or discarded — no unvalidated noise is emitted.

**Weight Encryption** — Neural network parameters are encrypted with AES-GCM using rotating keys derived from the host hardware fingerprint. Override with `THALOS_HARDWARE_ID` for cluster/CI deployments.

---

## Repository Layout

```
MNN/
├── api.py                        # FastAPI application (REST API entry point)
├── main.py                       # CLI entry point and pipeline orchestration
├── config.py                     # Configuration loaded from environment variables
├── middleware.py                  # ThalosBridge — real PostgreSQL bridge (psycopg2)
├── auth_utils.py                 # JWT helpers for operator authentication
├── logging_config.py             # Structured logging setup
├── security.py                   # Rate limiter, security headers, input validation
├── metrics.py                    # Prometheus-style metrics collection
├── feedback.py                   # Feedback storage helpers
├── weight_encryptor.py            # AES-GCM hardware-bound weight encryption
├── infra_status.py               # Infrastructure health checks (postgres/redis/minio/keycloak)
│
├── mnn_pipeline/                 # 7-stage deterministic query pipeline
│   ├── query_normalizer.py
│   ├── constraint_generator.py
│   ├── index_mapper.py
│   ├── sequence_generator.py
│   ├── analyzer.py
│   ├── scorer.py
│   └── output_handler.py
│
├── mnn/                          # Core MNN library
│   ├── babel_siphon.py           # Babel Siphon public API
│   ├── pipeline.py               # High-level pipeline entry point
│   ├── core/                     # Seed registry, SHA-256 deterministic hashing
│   ├── ir/                       # Pydantic IR models (ConstraintSchema, BreachCoordinates…)
│   ├── solver/                   # Z3 SMT solver integration
│   ├── scoring/                  # Candidate ranker
│   ├── deterministic/            # Lifecycle, RNG, basile coord gen, replay, audit log
│   ├── ucs/                      # Library of Sense (UCS) kernel integration
│   ├── control/                  # Neuro-symbolic control plane
│   ├── guard/                    # Logic guard
│   ├── verification/             # Formal verifier
│   ├── search/                   # Neuro-symbolic search
│   └── codegen/                  # Virtuoso code generation
│
├── src/                          # Original Python modules (legacy path)
│   ├── permutation/engine.py     # Permutation generator + 3-stage refinement
│   ├── mind/llm_handler.py       # Geometric embeddings, semantic sieve, text generation
│   ├── encryption/weight_encryptor.py
│   ├── buffer/relational_buffer.py
│   └── thalos/linear_algebra.py
│
├── include/mnn_core.hpp          # C++17 tensor math core (broadcasting, matmul, embeddings)
├── src/mnn_core.cpp              # C++ implementation
│
├── frontend/                     # Operator dashboard (React + Vite)
├── tools/                        # CLI utilities (find_coherent_page.py, thalos_cli.py…)
├── sql/                          # DDL schemas
├── tests/                        # Python test suite (pytest)
├── docs/                         # Additional documentation
├── devops/                       # Nix flake, hermetic Dockerfiles, lock files
│
├── Dockerfile                    # Production Docker image
├── docker-compose.yml            # Full stack: API + PostgreSQL + Redis + MinIO + Keycloak
├── Makefile                      # Build, test, lint, smoke, and deploy targets
├── pyproject.toml                # Project metadata and pytest configuration
├── requirements.txt              # Python runtime dependencies
├── ARCHITECTURE.md               # Detailed technical architecture documentation
└── BABEL_SIPHON_README.md        # Babel Siphon pipeline documentation
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- (Optional) Docker + Docker Compose for containerised deployment
- (Optional) PostgreSQL for persistent storage

### Install

```bash
# Clone the repository
git clone https://github.com/XxxGHOSTX/MNN.git
cd MNN

# Copy and edit environment configuration
cp .env.example .env

# Install Python dependencies
pip install -r requirements.txt
```

---

## Usage

### Command-Line Interface

Run the interactive query CLI:

```bash
python main.py
```

Example session:

```
============================================================
MNN Knowledge Engine - Query Interface
============================================================

Enter your query: artificial intelligence

Processing query: 'artificial intelligence'

Top 10 Results:
------------------------------------------------------------
1. BOOK 0: ARTIFICIAL INTELLIGENCE CONTINUES WITH MORE CONTENT HERE
2. BOOK 23: CONTENT BEFORE ARTIFICIAL INTELLIGENCE AND CONTENT AFTER
...
------------------------------------------------------------
Total results found: 10
```

### REST API

Start the API server:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Service information |
| `/health` | GET | Health check + cache statistics |
| `/query` | POST | Submit a query, receive ranked results |
| `/suggestions` | GET | Query suggestions |
| `/auth/login` | POST | Obtain operator JWT token |
| `/auth/me` | GET | Authenticated operator profile |
| `/dashboard/overview` | GET | Operator dashboard data |
| `/docs` | GET | Interactive Swagger UI |

#### Query example (Python)

```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"query": "artificial intelligence"}
)

data = response.json()
print(f"Normalized query: {data['query']}")
for item in data["results"]:
    print(f"  [{item['score']:.3f}] {item['sequence']}")
```

#### Query example (cURL)

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "quantum computing"}'
```

#### Response schema

```json
{
  "query": "QUANTUM COMPUTING",
  "results": [
    { "sequence": "BOOK 0: QUANTUM COMPUTING ...", "score": 0.952 }
  ],
  "count": 5
}
```

**Status codes:** `200` success · `400` empty query · `422` validation error · `500` pipeline error

### Babel Siphon Pipeline

The Babel Siphon is an SMT-Arbiter pipeline that guarantees every output satisfies formal constraints (length, token containment, character set, code invariants). It never emits unvalidated noise.

**CLI usage:**

```bash
# Generate a validated text page containing "hello world"
python tools/find_coherent_page.py "hello world" --seed 42

# Generate validated Python code
python tools/find_coherent_page.py "def fibonacci" --domain code --seed 1
```

**Python API:**

```python
from mnn.babel_siphon import run_babel_siphon

result = run_babel_siphon("hello world", seed=42)
if result.status == "ok":
    for candidate in result.candidates:
        print(candidate.text)
else:
    print("No valid candidates found")
```

See [BABEL_SIPHON_README.md](BABEL_SIPHON_README.md) for full documentation.

### Operator Dashboard

The repository includes a deployable React/Vite operator dashboard under `frontend/` with authentication, a query runner, and an infrastructure status panel.

**Run locally:**

```bash
# Backend (in one terminal)
uvicorn api:app --host 0.0.0.0 --port 8000

# Frontend (in a second terminal)
cd frontend
yarn install
yarn dev
```

Default operator credentials (change in production):

| Variable | Default |
|---|---|
| `MNN_ADMIN_USERNAME` | `admin` |
| `MNN_ADMIN_PASSWORD` | `admin123!` |

Dashboard routes:

- `/auth/login` — operator login
- `/auth/me` — authenticated profile
- `/dashboard/overview` — main overview
- `/query` — query runner
- Infrastructure panel with graceful fallback (postgres, redis, minio, keycloak)

**Deploy to Vercel + external backend:**

```bash
# Deploy frontend/ to Vercel
# Set VITE_BACKEND_URL in Vercel environment to your backend URL
```

---

## Configuration

All settings are loaded from environment variables. Copy `.env.example` to `.env` and edit as needed.

### Core settings

| Variable | Default | Description |
|---|---|---|
| `THALOS_DB_DSN` | _(unset)_ | PostgreSQL DSN. If unset, the buffer operates in mock/in-memory mode |
| `THALOS_DB_CONNECT_TIMEOUT` | `10` | DB connection timeout in seconds |
| `THALOS_HARDWARE_ID` | _(auto)_ | Hardware fingerprint for weight encryption. Override for cluster/CI |
| `MNN_API_HOST` | `127.0.0.1` | API bind address (`0.0.0.0` required inside Docker) |
| `MNN_API_PORT` | `8000` | API port |
| `ENVIRONMENT` | `production` | Environment name (`production`, `staging`, `development`) |

### Authentication

| Variable | Default | Description |
|---|---|---|
| `API_AUTH_ENABLED` | `false` | Set `true` to require JWT on protected endpoints |
| `MNN_AUTH_SECRET` | _(required in production)_ | JWT signing secret — **always override this** |
| `MNN_ADMIN_USERNAME` | `admin` | Operator login username |
| `MNN_ADMIN_PASSWORD` | `admin123!` | Operator login password — **always override this** |
| `MNN_TOKEN_EXPIRE_MINUTES` | `120` | JWT expiry in minutes |

### Security & Rate Limiting

| Variable | Default | Description |
|---|---|---|
| `MAX_QUERY_LENGTH` | `4096` | Maximum query length (characters) |
| `RATE_LIMIT_ENABLED` | `true` | Enable/disable rate limiting |
| `RATE_LIMIT_REQUESTS` | `100` | Max requests per window |
| `RATE_LIMIT_WINDOW` | `60` | Rate limit window in seconds |

### Logging & Caching

| Variable | Default | Description |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Python log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_FORMAT` | _(standard)_ | Python log format string |
| `CACHE_SIZE` | `1024` | In-memory LRU cache size |

### Deterministic Runtime

| Variable | Default | Description |
|---|---|---|
| `DETERMINISTIC_MODE` | `true` | Enable deterministic-mode enforcement |
| `DETERMINISTIC_ROOT_SEED` | `2026` | Root RNG seed for all deterministic operations |
| `DETERMINISTIC_AUDIT_LOG_PATH` | `logs/deterministic/run.jsonl` | Hash-chained JSONL audit log path |

### Optional service integrations (Docker Compose)

| Variable | Default | Description |
|---|---|---|
| `REDIS_URL` | `redis://redis:6379/0` | Redis cache URL |
| `MINIO_ENDPOINT` | `http://minio:9000` | MinIO object storage endpoint |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO access key |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO secret key |
| `KEYCLOAK_URL` | `http://keycloak:8080` | Keycloak identity provider URL |
| `KEYCLOAK_REALM` | `master` | Keycloak realm |

---

## Architecture

```
THALOS / MNN Architecture
│
├── Permutation Engine          (src/permutation/engine.py)
│   ├── Stage 1: 29-char permutation generation
│   ├── Stage 2: Mathematical refinement (3 iterations)
│   └── Stage 3: Conceptual filtering / pattern extraction
│
├── MNN Pipeline                (mnn_pipeline/)
│   ├── Query Normalizer        → uppercase, strip, collapse whitespace
│   ├── Constraint Generator    → min/max length bounds
│   ├── Index Mapper            → 1000 deterministic candidate positions
│   ├── Sequence Generator      → "book" content at each index
│   ├── Analyzer                → filter by pattern, length, uniqueness
│   ├── Scorer                  → center-weighted relevance ranking
│   └── Output Handler          → format top-N results
│
├── Babel Siphon                (mnn/babel_siphon.py, mnn/solver/)
│   ├── Formalization           → ConstraintSchema (Pydantic IR)
│   ├── Generation              → deterministic semantic lattice
│   ├── SMT Validation          → Z3 constraint checking
│   ├── Repair                  → BreachCoordinates-guided auto-repair
│   └── Ranking                 → validated candidate scoring
│
├── Deterministic Runtime       (mnn/deterministic/)
│   ├── Lifecycle state-machine with halt snapshots
│   ├── Cross-language RNG descriptor parity (Python / C++)
│   ├── Basile coordinate-to-text generation (base-29)
│   ├── Hash-chained JSONL audit log + replay validation
│   └── Formal lifecycle proofs via Z3
│
├── C++ Core                    (include/mnn_core.hpp, src/mnn_core.cpp)
│   ├── Tensor math (broadcasting, matmul)
│   └── Geometric Character Embedding
│
├── PostgreSQL Relational Buffer (middleware.py, sql/)
│   ├── manifold_coordinates    → high-confidence responses
│   ├── void_logs               → knowledge gaps / noise tracking
│   └── weights_vault           → hardware-bound encrypted weight storage
│
└── Operator Layer              (api.py, frontend/)
    ├── FastAPI REST API with JWT auth, rate limiting, security headers
    └── React/Vite operator dashboard
```

For a deeper dive see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Development

### Install dev dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

### Lint

```bash
make lint
# or directly:
python -m compileall .
```

### Test

```bash
# Run the full test suite
python -m pytest

# Run with coverage
python -m pytest --cov=mnn_pipeline --cov=mnn --cov-report=term-missing

# Run a specific module
python -m pytest tests/test_pipeline.py -v
python -m pytest tests/test_babel_siphon.py -v
```

### Safety & Security Checks

```bash
# Dependency vulnerability audit (requires pip-audit)
pip install pip-audit
pip-audit

# Verify no known-vulnerable packages are installed:
pip-audit --format json -o sbom-audit.json

# HTML sanitisation (bleach must be imported where user HTML is processed):
python -c "import bleach; print(bleach.__version__)"
```

> **Note on CodeQL**: The `.github/workflows/codeql.yml` workflow runs CodeQL
> analysis on every push and pull request.  To avoid SARIF upload conflicts,
> ensure that GitHub's built-in "Default setup" for Code Scanning is **disabled**
> in repository Settings → Code security and analysis → Code scanning.
> See [`DECISION.md`](DECISION.md) for full details.

### Verify (lint + test + C++ sanity compile)

```bash
make verify
```

### C++ Core

Sanity-compile the C++ tensor core:

```bash
g++ -std=c++17 -Iinclude -c src/mnn_core.cpp
# or with deterministic compiler flags:
make cpp-deterministic
```

### Deterministic Runtime Checks

```bash
# Lifecycle formal proofs (Z3)
make verify-lifecycle

# Python/C++ RNG descriptor parity
make cross-language-rng-check

# Deterministic output benchmark
make benchmark-deterministic

# Reproducibility check
python tools/reproducibility_check.py --query "deterministic systems"
```

### Database Setup (optional)

For persistent storage, provision PostgreSQL and initialise the schemas:

```bash
export THALOS_DB_DSN=postgresql://thalos:password@localhost:5432/thalos

# Apply schemas
psql -U thalos -d thalos -f sql/relational_buffer_schema.sql
psql -U thalos -d thalos -f thalos_db_schema.sql

# Or via Python:
python -c "from middleware import ThalosBridge; ThalosBridge().apply_schema()"
```

---

## Docker & Deployment

### Build and run

```bash
# Build the image
make build
# or:
docker build -t mnn-pipeline:latest .

# Run the API on port 8000
docker run -p 8000:8000 mnn-pipeline:latest

# With environment variables
docker run -p 8000:8000 \
  -e THALOS_DB_DSN="postgresql://user:pass@host:5432/db" \
  -e MNN_AUTH_SECRET="my-secret" \
  mnn-pipeline:latest
```

### Docker Compose (full stack)

```bash
# Start API + PostgreSQL + Redis + MinIO + Keycloak
make compose-up
# or:
docker compose up -d

# Stop
make compose-down
```

Services:

| Service | Port | Description |
|---|---|---|
| `api` | 8000 | MNN FastAPI service |
| `db` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Redis cache |
| `minio` | 9000 / 9001 | Object storage + console |
| `keycloak` | 8080 | Identity provider |

The API can run standalone — all external services fall back gracefully if not configured.

### Smoke Test

```bash
make smoke
```

This builds the image, starts a container, waits for the API to be ready, sends a test query, verifies the response, then stops and cleans up.

### End-to-end smoke test (manual)

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 &

# Health check
curl http://localhost:8000/health

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "hello world"}'
```

### Production Checklist

- [ ] Change `MNN_AUTH_SECRET`, `MNN_ADMIN_USERNAME`, `MNN_ADMIN_PASSWORD` from defaults
- [ ] Set `API_AUTH_ENABLED=true` to require JWT on protected endpoints
- [ ] Deploy behind a TLS-terminating reverse proxy (nginx, traefik)
- [ ] Use strong PostgreSQL credentials and enable SSL (`?sslmode=require`)
- [ ] Set `THALOS_HARDWARE_ID` to a stable value in clustered/CI environments
- [ ] Monitor `/health` and set up alerting on container restarts

### Vercel + External Backend

1. Deploy `frontend/` to Vercel
2. Set `VITE_BACKEND_URL` in the Vercel project environment to your backend URL
3. Configure `CORS` origins in the backend to match your Vercel domain

---

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request to `main`.

### Jobs

| Job | Trigger | What it does |
|---|---|---|
| **lint** | every push/PR | `python -m compileall .` — validates Python syntax |
| **test** | every push/PR | `pytest` on Python 3.12 — all tests must pass |
| **docker-smoke** | every push/PR | Builds image, starts container, tests `/health` and `/query` |
| **deploy** | push to `main` only | Builds and pushes Docker image to GHCR with `latest` + commit SHA tags |

Actions used: `actions/checkout@v4`, `actions/setup-python@v5`, `docker/setup-buildx-action@v3`.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## References

- [libraryofbabel.info](https://libraryofbabel.info) — inspiration for the permutation logic
- [Z3 SMT Solver](https://github.com/Z3Prover/z3) — constraint validation in Babel Siphon
- [Geometric Deep Learning](https://geometricdeeplearning.com/) — manifold-based embeddings
- [ARCHITECTURE.md](ARCHITECTURE.md) — detailed technical architecture
- [BABEL_SIPHON_README.md](BABEL_SIPHON_README.md) — Babel Siphon pipeline documentation

