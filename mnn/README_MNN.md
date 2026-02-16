# MNN Engine - Matrix Neural Network

A deterministic, modular query processing engine with strict typing and guaranteed reproducibility.

## Architecture Overview

The MNN Engine implements a pipeline-based architecture with the following stages:

1. **Query Normalization** - Uppercase, strip non-alphanumerics, collapse whitespace
2. **Constraint Generation** - Create processing constraints from normalized query
3. **Index Mapping** - Map constraints to deterministic indices
4. **Sequence Generation** - Generate sequences with embedded patterns
5. **Sequence Analysis** - Filter sequences by pattern and length constraints
6. **Scoring & Ranking** - Score by pattern centrality and rank deterministically

### Determinism Guarantees

- **Identical Inputs → Identical Outputs**: Same query always produces the same results in the same order
- **No Randomness**: All operations are deterministic
- **Stable Ordering**: Concurrent operations maintain deterministic output order
- **Cache Protection**: Deep copy protection prevents cached result mutation

### Pipeline Stages

```
Query Input
    ↓
normalize_query() - Uppercase, strip, collapse whitespace
    ↓
generate_constraints() - Pattern, min/max length
    ↓
map_constraints_to_indices() - Deterministic index generation
    ↓
generate_sequences() - Pattern embedding (ThreadPoolExecutor with stable order)
    ↓
analyze_sequences() - Filter by pattern presence and length
    ↓
score_and_rank() - Score by centrality, rank descending
    ↓
Results (list[dict])
```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r mnn/requirements_mnn.txt
```

## Usage

### CLI Usage

Run the interactive command-line interface:

```bash
python -m mnn.main
```

Or from the repository root:

```bash
cd mnn
python main.py
```

Example session:
```
MNN Engine - Matrix Neural Network Query Processor
==================================================
Enter query: hello world

Processing...

Top 10 results:
--------------------------------------------------
1. HELLO WORLDXXXXXXXX...
2. XHELLO WORLDXXXXXXX...
...

Total results: 250
```

### API Usage

Start the FastAPI server:

```bash
uvicorn mnn.api:app --reload
```

Or with custom host/port:

```bash
uvicorn mnn.api:app --host 127.0.0.1 --port 8000
```

#### API Endpoints

**POST /query**

Process a query through the MNN pipeline.

Request:
```json
{
  "query": "hello world"
}
```

Response:
```json
{
  "results": [
    {
      "sequence": "HELLO WORLDXXXXXXXX...",
      "score": 0.952380952380952
    },
    ...
  ],
  "count": 250
}
```

**GET /**

API information and available endpoints.

**GET /health**

Health check endpoint.

### Python API

Use the MNN engine programmatically:

```python
from mnn.pipeline import run_pipeline

# Process a query
results = run_pipeline("hello world")

# Results is a list of dicts with 'sequence' and 'score'
for result in results[:5]:
    print(f"Score: {result['score']:.4f}")
    print(f"Sequence: {result['sequence']}")
```

## Testing

### Run All Tests

```bash
python -m unittest discover mnn/tests
```

### Run Specific Test Modules

```bash
# Pipeline tests
python -m unittest mnn.tests.test_pipeline

# API tests
python -m unittest mnn.tests.test_api
```

### Test Coverage

Tests cover:
- Query normalization (including empty query validation)
- Constraint generation
- Index mapping determinism
- Sequence generation (length and pattern embedding)
- Sequence filtering
- Scoring and ranking (score calculation and ordering)
- Pipeline determinism (repeated queries produce identical results)
- API endpoints and error handling

## Caching

The MNN engine uses LRU caching at the pipeline level:

- **Cache Size**: 128 queries (configurable)
- **Cache Key**: Normalized query string
- **Cache Protection**: Deep copy on retrieval prevents mutation
- **Clear Cache**: Call `run_pipeline.cache_clear()`

Example:
```python
from mnn.pipeline import run_pipeline

# First call - processes through pipeline
results1 = run_pipeline("test")

# Second call - returns cached result
results2 = run_pipeline("test")

# Clear cache if needed
run_pipeline.cache_clear()
```

## Module Reference

### Core Modules

- **query_normalizer.py** - `normalize_query(query: str) -> str`
- **constraint_generator.py** - `generate_constraints(normalized_query: str) -> dict`
- **index_mapper.py** - `map_constraints_to_indices(constraints: dict) -> list[int]`
- **sequence_generator.py** - `generate_sequences(indices: list[int], constraints: dict) -> list[str]`
- **analyzer.py** - `analyze_sequences(sequences: list[str], constraints: dict) -> list[str]`
- **scorer.py** - `score_and_rank(sequences: list[str], constraints: dict) -> list[dict]`

### Support Modules

- **cache.py** - Caching utilities with deep copy protection
- **output_handler.py** - Formatted output for CLI
- **pipeline.py** - Pipeline orchestration with caching
- **main.py** - CLI entrypoint
- **api.py** - FastAPI web service

## Deterministic Behavior Notes

### Concurrency

The sequence generator uses `ThreadPoolExecutor` for performance but maintains deterministic ordering:

1. Indices are sorted before processing
2. Results are collected into a dictionary keyed by index
3. Final results are returned in sorted index order

### Tie-Breaking

When multiple sequences have identical scores, the scorer uses the original sequence index for deterministic tie-breaking.

### Caching Strategy

Caching is performed at the pipeline level only. Individual stage functions don't use `@lru_cache` when they accept or return unhashable types (like dicts).

## Non-Destructive Integration

This MNN engine is designed as an **additive** component:

- ✅ All files are new under `mnn/` directory
- ✅ No existing repository files are modified
- ✅ Independent requirements file (`requirements_mnn.txt`)
- ✅ Self-contained with no external dependencies on existing code

## License

Same as parent repository.

## Version

1.0.0
