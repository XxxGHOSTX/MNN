# MNN: Deterministic Matrix Neural Network Engine

A fully deterministic, type-safe pipeline for query processing, constraint generation, sequence generation, analysis, scoring, and ranking. All operations produce identical results for identical inputs with no randomness or side effects (except defined I/O).

## Overview

The MNN engine implements a deterministic pipeline that processes text queries through multiple stages to generate, analyze, and rank sequences based on pattern matching and centering scores.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MNN PIPELINE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Query Input                                                     │
│      ↓                                                           │
│  ┌──────────────────┐                                           │
│  │ Query Normalizer │  Uppercase, strip non-alphanumeric,       │
│  │                  │  collapse whitespace, validate non-empty  │
│  └────────┬─────────┘                                           │
│           ↓                                                      │
│  ┌──────────────────┐                                           │
│  │   Constraint     │  Extract pattern, min_length,             │
│  │   Generator      │  max_length from normalized query         │
│  └────────┬─────────┘                                           │
│           ↓                                                      │
│  ┌──────────────────┐                                           │
│  │  Index Mapper    │  Generate candidate indices based on      │
│  │  (LRU Cached)    │  pattern length: range(0, 1000, step)     │
│  └────────┬─────────┘                                           │
│           ↓                                                      │
│  ┌──────────────────┐                                           │
│  │   Sequence       │  Embed pattern at deterministic           │
│  │   Generator      │  positions within filler strings          │
│  │  (Concurrent)    │  (ordering preserved)                     │
│  └────────┬─────────┘                                           │
│           ↓                                                      │
│  ┌──────────────────┐                                           │
│  │    Analyzer      │  Filter sequences by pattern presence     │
│  │                  │  and length constraints                   │
│  └────────┬─────────┘                                           │
│           ↓                                                      │
│  ┌──────────────────┐                                           │
│  │  Scorer/Ranker   │  Score by pattern centering,              │
│  │                  │  rank with deterministic tie-breaking     │
│  └────────┬─────────┘                                           │
│           ↓                                                      │
│  Ranked Results (List[Dict])                                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### Determinism Guarantees
- **No randomness**: All operations are fully deterministic
- **Stable ordering**: Concurrent operations preserve input order
- **Deterministic tie-breaking**: Scores use original index for stable sorting
- **Reproducible caching**: LRU cache with deep-copy protection
- **Identical results**: Same query always produces same output

### Type Safety
- Full type hints for all functions (Python 3.12+)
- Pydantic models for API request/response validation
- Strict validation of inputs and constraints

### Performance
- LRU caching for frequently repeated queries
- ThreadPoolExecutor for concurrent sequence generation
- Efficient index mapping with cached helpers

## Module Descriptions

### Core Pipeline Modules

1. **query_normalizer.py**
   - Normalizes queries to canonical form
   - Uppercase, alphanumeric, whitespace collapsed
   - Validates non-empty results

2. **constraint_generator.py**
   - Extracts constraints from normalized queries
   - Generates pattern, min_length, max_length

3. **index_mapper.py**
   - Maps constraints to candidate indices
   - Uses LRU-cached helper for performance

4. **sequence_generator.py**
   - Generates sequences with embedded patterns
   - Concurrent generation with ordering preservation
   - Deterministic position calculation

5. **analyzer.py**
   - Filters sequences by pattern and length
   - Preserves input order

6. **scorer.py**
   - Scores sequences by pattern centering
   - Ranks with deterministic tie-breaking
   - Higher scores = more centered patterns

7. **output_handler.py**
   - Formats results for display
   - Numbered output (1..N)

### Orchestration

8. **cache.py**
   - Deterministic LRU caching
   - Deep-copy protection for mutable results
   - Global cache clearing for tests

9. **pipeline.py**
   - End-to-end pipeline orchestration
   - Cached execution for performance
   - Coordinates all stages

### User Interfaces

10. **main.py**
    - Command-line interface
    - Interactive query processing
    - Formatted console output

11. **api.py**
    - FastAPI REST API
    - JSON request/response
    - Health check endpoint

## Installation & Setup

### Prerequisites
- Python 3.12 or higher
- pip package manager

### Quick Start

1. **Create virtual environment (recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   cd mnn
   pip install -r requirements_mnn.txt
   ```

3. **Verify installation**
   ```bash
   python -c "import fastapi, uvicorn, httpx; print('All dependencies installed')"
   ```

## Usage

### Command-Line Interface (CLI)

Run the interactive CLI:

```bash
python -m mnn.main
```

Or directly:

```bash
python mnn/main.py
```

Example session:
```
MNN Deterministic Pipeline - CLI
===================================

Enter your query (or Ctrl+C to exit): test query

Top 10 Results:
---------------
1. XXXXXXtestXXXXXXXXXXX
2. XXXXXXXXXXtestXXXXXXX
3. XXXXtestXXXXXXXXXXXXX
...

Enter your query (or Ctrl+C to exit): ^C
Exiting...
```

### REST API

#### Start the API server:

```bash
uvicorn mnn.api:app --reload
```

Or with custom host/port:

```bash
uvicorn mnn.api:app --host 0.0.0.0 --port 8080
```

#### API Endpoints:

**GET /**
- Root endpoint with API information

**GET /health**
- Health check endpoint

**POST /query**
- Process query and return ranked results

#### Example API Usage:

```bash
# Process a query
curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "test query"}'

# Response:
{
  "query": "test query",
  "normalized_query": "TEST QUERY",
  "ranked": [
    {
      "sequence": "XXXXXXtestXXXXXXXXXXX",
      "score": 0.952380952380952
    },
    ...
  ],
  "count": 200
}
```

#### Python API Client:

```python
import httpx

response = httpx.post(
    "http://localhost:8000/query",
    json={"query": "test query"}
)
print(response.json())
```

### Programmatic Usage

```python
from mnn.pipeline import run_pipeline

# Run pipeline
results = run_pipeline("test query")

# Results are cached - subsequent calls return cached results
results_cached = run_pipeline("test query")
assert results == results_cached  # True

# Clear cache if needed
from mnn.cache import clear_cache
clear_cache()
```

## Testing

### Run All Tests

```bash
python -m unittest discover mnn/tests
```

Or with verbose output:

```bash
python -m unittest discover mnn/tests -v
```

### Run Specific Test Files

```bash
# Test pipeline components
python -m unittest mnn.tests.test_pipeline

# Test API endpoints
python -m unittest mnn.tests.test_api
```

### Test Coverage

The test suite includes:
- Query normalization (including empty query validation)
- Constraint generation
- Index mapping (determinism)
- Sequence generation (pattern presence, length constraints)
- Sequence analysis (filtering)
- Scoring and ranking (deterministic ordering)
- End-to-end pipeline (determinism on repeated calls)
- API endpoints (deterministic responses)

## Determinism Notes

### What Makes MNN Deterministic?

1. **No Random Operations**
   - No `random` module usage
   - No non-deterministic algorithms
   - No time-based variations

2. **Stable Ordering**
   - All sequences processed in sorted index order
   - ThreadPoolExecutor operations preserve ordering
   - Sorting uses deterministic tie-breaking

3. **Reproducible Caching**
   - LRU cache ensures identical queries return identical results
   - Deep-copy protection prevents cache corruption
   - Cache keyed only by input query string

4. **Explicit Input/Output**
   - Pure functions (no hidden state mutations)
   - Side effects limited to defined I/O (print, API responses)
   - All dependencies injected explicitly

### Verifying Determinism

```python
from mnn.pipeline import run_pipeline

# Run same query multiple times
results = [run_pipeline("test") for _ in range(10)]

# Verify all results are identical
assert all(r == results[0] for r in results)
```

## Performance Considerations

- **Caching**: First query executes full pipeline; subsequent identical queries served from cache
- **Concurrency**: Sequence generation uses ThreadPoolExecutor for parallelism
- **Index Mapping**: LRU-cached for frequently used patterns
- **Memory**: Cache size configurable (default: 128 entries)

## Troubleshooting

### Empty Query Error
```
Error: Normalized query is empty
```
**Solution**: Ensure query contains at least one alphanumeric character

### API Connection Refused
```
ConnectionError: Connection refused
```
**Solution**: Start API server with `uvicorn mnn.api:app --reload`

### Import Errors
```
ModuleNotFoundError: No module named 'fastapi'
```
**Solution**: Install dependencies: `pip install -r mnn/requirements_mnn.txt`

## Project Structure

```
mnn/
├── __init__.py                 # Package initialization
├── query_normalizer.py         # Query normalization
├── constraint_generator.py     # Constraint extraction
├── index_mapper.py             # Index mapping (cached)
├── sequence_generator.py       # Sequence generation
├── analyzer.py                 # Sequence filtering
├── scorer.py                   # Scoring and ranking
├── output_handler.py           # Output formatting
├── cache.py                    # Deterministic caching
├── pipeline.py                 # Pipeline orchestration
├── main.py                     # CLI interface
├── api.py                      # REST API
├── requirements_mnn.txt        # Python dependencies
├── README_MNN.md              # This file
└── tests/
    ├── test_pipeline.py       # Pipeline tests
    └── test_api.py            # API tests
```

## Credits

**Author**: MNN Engine Contributors  
**License**: MIT  
**Version**: 1.0.0

## Contributing

This is a fully deterministic engine with strict requirements:
- All functions must be deterministic
- No randomness or time-based variations
- Complete type hints and docstrings
- No TODOs or stub implementations
- Comprehensive test coverage

## Future Enhancements

Potential non-breaking additions:
- Additional scoring algorithms (maintaining determinism)
- Configuration file support
- More output formats (JSON, CSV)
- Batch query processing
- Performance metrics and profiling

---

For questions or issues, please refer to the main repository documentation.
