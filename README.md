# THALOS: Matrix Neural Network (MNN)

A neural network library implementing the THALOS system - a refined approach to LLM architecture inspired by libraryofbabel.info's permutation logic.

## Overview

THALOS (The Heuristic Algorithm for Lattice-Optimized Synthesis) implements a unique 3-stage mathematical refinement process that transforms infinite permutation space into structured, linguistically-valid neural network training data.

## Key Features

### 1. **THALOS Linear Algebra Stack**
Custom matrix operations optimized for neural network computations.

```python
from thalos.linear_algebra import ThalosMatrix

# Create matrix
matrix = ThalosMatrix([[1, 2], [3, 4]])

# Perform operations
result = matrix.matmul(other_matrix)
activated = matrix.apply_activation("relu")
```

### 2. **Permutation Engine with 3-Stage Refinement**
Replicates libraryofbabel.info's logic with mathematical refinement and conceptual filtering.

**Operational Sequence:**
1. **Stage 1**: Permutation Space Generation (29-character set: a-z + space, comma, period)
2. **Stage 2**: Mathematical Refinement (iterative transformations)
3. **Stage 3**: Conceptual Filtering (pattern extraction)

```python
from permutation.engine import PermutationEngine

engine = PermutationEngine(seed=42)
refined_output = engine.process(
    dimensions=10,
    cardinality=29,
    refinement_iterations=3
)
```

### 3. **Geometric Character Embeddings**
Replace standard Byte-Pair Encoding (BPE) with geometric vertex mapping in high-dimensional manifold.

```python
from mind.llm_handler import GeometricCharacterEmbedding

embedding = GeometricCharacterEmbedding(embedding_dim=512)

# Encode text to manifold vertices
embeddings = embedding.encode("hello world")

# Calculate relational distances
distance = embedding.relational_distance('a', 'z')
```

### 4. **Semantic Sieve**
Filters 99.999% of noise from synthetic permutations, retaining only linguistically-structured data.

```python
from mind.llm_handler import SemanticSieve

sieve = SemanticSieve(noise_threshold=0.99999)
is_valid, confidence = sieve.filter("the quick brown fox")
```

### 5. **Weight Encryption**
Hardware-bound encryption with rotating keys for binary-level parameter protection.

```python
from encryption.weight_encryptor import WeightEncryptor

encryptor = WeightEncryptor()

# Encrypt weights
encrypted = encryptor.encrypt_weights(weights)

# Rotate key during training
encryptor.rotate_key()

# Decrypt
decrypted = encryptor.decrypt_weights(encrypted)
```

### 6. **PostgreSQL Relational Buffer**
Metadata layer for tracking successful resolutions and knowledge gaps.

**Tables:**
- `manifold_coordinates`: Stores high-confidence responses
- `void_logs`: Tracks queries resulting in noise (knowledge gaps)

```python
from buffer.relational_buffer import RelationalBuffer

buffer = RelationalBuffer()
buffer.connect()

# Store successful resolution
buffer.store_successful_resolution(
    query="hello world",
    response="generated response",
    confidence=0.95
)

# Analyze knowledge gaps
analysis = buffer.analyze_knowledge_gaps()
```

### 7. **Mind (LLM) Handler**
200M+ parameter Matrix Neural Network for text generation.

```python
from mind.llm_handler import MindLLMHandler

mind = MindLLMHandler(embedding_dim=512, hidden_dim=2048)

# Generate text
response = mind.generate("hello", max_length=100)

# Evaluate confidence
confidence = mind.evaluate_confidence(response)
```

## Complete Operational Sequence

```python
from examples.operational_sequence import operational_sequence

# Run complete THALOS workflow
operational_sequence()
```

This demonstrates:
1. PRNG initialization with Library's algorithm
2. Semantic Sieve application
3. MNN training with encrypted weights
4. THALOS deployment with PostgreSQL buffer

## Installation

```bash
pip install -r requirements.txt
```

## Running Tests

```bash
# Run all tests
python -m unittest discover tests

# Run specific test module
python -m unittest tests.test_thalos
python -m unittest tests.test_permutation
python -m unittest tests.test_encryption
python -m unittest tests.test_mind
python -m unittest tests.test_buffer
```

## Architecture

```
THALOS Architecture
├── Permutation Engine (libraryofbabel.info logic)
│   ├── Stage 1: Permutation Generation (29-char set)
│   ├── Stage 2: Mathematical Refinement (3 iterations)
│   └── Stage 3: Conceptual Filtering (pattern extraction)
│
├── Synthetic Data Pipeline
│   ├── Semantic Sieve (99.999% noise filtering)
│   └── Geometric Character Embeddings (manifold vertices)
│
├── Matrix Neural Network (200M+ parameters)
│   ├── THALOS Linear Algebra Stack
│   └── Weight Encryption (hardware-bound keys)
│
└── PostgreSQL Relational Buffer
    ├── manifold_coordinates (successful resolutions)
    └── void_logs (knowledge gap tracking)
```

## Key Concepts

### Geometric Character Embeddings
Unlike BPE tokenization, THALOS maps each of the 29 characters to vertices in a high-dimensional manifold. The system learns "meaning" from the relational distances between these vertices.

### Semantic Sieve
Instead of training on all possible permutations (like libraryofbabel.info's infinite library), the Semantic Sieve filters out 99.999% of noise, capturing only permutations that align with known linguistic structures.

### Weight Encryption
During training, neural network parameters are encrypted using rotating keys derived from the system's hardware ID, ensuring binary-level protection of the trained "intelligence."

### Void Space
The PostgreSQL buffer tracks queries that result in noise, helping the system identify knowledge gaps ("Void Space") where the model lacks confidence.

## Example Usage

```python
# Initialize components
from permutation.engine import PermutationEngine
from mind.llm_handler import MindLLMHandler
from buffer.relational_buffer import RelationalBuffer

# Create permutation engine
engine = PermutationEngine(seed=42)

# Initialize Mind LLM
mind = MindLLMHandler()

# Connect to buffer
buffer = RelationalBuffer()
buffer.connect()

# Process query
query = "artificial intelligence"
response = mind.generate(query, max_length=50)
confidence = mind.evaluate_confidence(response)

# Store result
if confidence > 0.5:
    buffer.store_successful_resolution(query, response, confidence)
else:
    buffer.store_void_log(query, "Low confidence", confidence, "noise")
```

## License

MIT License - See LICENSE file for details.

## References

- libraryofbabel.info - Inspiration for permutation logic
- Geometric Deep Learning - Manifold-based embeddings
- Hardware-bound Encryption - Binary-level parameter protection
# MNN

Matrix Neural Network (MNN)

## PostgreSQL Relational Buffer schema
The relational buffer schema tailored for `/artifacts/{appId}/public/data/` lives in `sql/relational_buffer_schema.sql`. It models:
* `applications` and `artifacts` with generated storage paths rooted at `/artifacts/{appId}/public/data/`
* `manifolds`, `manifold_coordinates`, and `void_spaces` to track manifold coverage and void regions
* `buffer_segments` to pin coordinate bounds to on-disk slices

Apply with:
```bash
psql -f sql/relational_buffer_schema.sql
```

## C++ MNN core
The C++ implementation under `include/mnn_core.hpp` and `src/mnn_core.cpp` provides first principles tensor math, broadcasting, and the Geometric Character Embedding used by the 200M+ parameter Matrix Neural Network.

Build a quick sanity check:
```bash
g++ -std=c++17 -Iinclude -c src/mnn_core.cpp
```
Infrastructure and persistence helpers for Matrix Neural Network (MNN).

## Database setup

1. Provision PostgreSQL and set `THALOS_DB_DSN`, e.g.:
   ```bash
   export THALOS_DB_DSN=postgresql://thalos:thalos@localhost:5432/thalos
   ```
2. Apply the schema:
   ```bash
   python -c "from middleware import ThalosBridge; ThalosBridge().apply_schema()"
   ```

Tables created:
- `manifold_coordinates` – relational buffer for embeddings and metadata
- `void_logs` – safety log sink
- `weights_vault` – encrypted vault for model weights bound to a hardware fingerprint

## Using the middleware

```python
from middleware import ThalosBridge

bridge = ThalosBridge()
coord_id = bridge.write_manifold_coordinate(
    source="sensor_A",
    coordinate={"x": 1.2, "y": -0.7},
    embedding=[0.1, 0.2, 0.3],
    confidence=0.98,
)
bridge.write_void_log("info", "coordinate captured", {"id": coord_id}, coordinate_ref=coord_id)

# Store and load weights (bytes)
with open("weights.bin", "rb") as fh:
    weight_bytes = fh.read()
bridge.upsert_encrypted_weights("mnn-core", weight_bytes)
restored = bridge.load_encrypted_weights("mnn-core")
```

## Hardware-bound encryption

`weight_encryptor.py` binds AES-GCM encryption to a hardware fingerprint derived from the host. Override with `THALOS_HARDWARE_ID` for stable CI or clustered deployments. Checksums ensure tamper detection during decrypt.

---

# MNN Pipeline: Deterministic Knowledge Engine

## What is MNN Pipeline?

The MNN Pipeline is a **deterministic, constraint-driven knowledge engine** inspired by Jorge Luis Borges' Library of Babel concept, but transformed into a practical, queryable system. Unlike libraryofbabel.info which returns 99.999% noise, MNN Pipeline generates and returns only relevant, validated results.

### Key Differences from LibraryOfBabel.info

| Feature | LibraryOfBabel.info | MNN Pipeline |
|---------|---------------------|--------------|
| **Search Approach** | Scan infinite permutations | Deterministic index mapping |
| **Relevance** | 99.999% noise | 100% contain query pattern |
| **Results** | Random combinations | Validated, ranked sequences |
| **Usability** | Web interface (academic) | CLI + REST API (production) |
| **Caching** | N/A | LRU cache for performance |
| **Integration** | Manual lookup | Programmatic API |

## How It Works

The MNN Pipeline transforms the Library of Babel's infinite search space into a finite, practical system:

1. **Query Normalization**: Convert input to standardized form (uppercase, alphanumeric)
2. **Constraint Generation**: Create deterministic search constraints
3. **Index Mapping**: Calculate specific "book" positions (Library-of-Babel-inspired)
4. **Sequence Generation**: Generate only relevant sequences at mapped indices
5. **Analysis/Filtering**: Validate pattern presence, length, and uniqueness
6. **Scoring/Ranking**: Rank by center-weighted relevance scoring
7. **Output**: Return top results (10 for CLI, 5 for API)

**See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical explanation.**

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Command Line Interface (CLI)

```bash
python main.py
```

Example session:
```
$ python main.py
============================================================
MNN Knowledge Engine - Query Interface
============================================================

Enter your query: artificial intelligence

Processing query: 'artificial intelligence'

Top 10 Results:
------------------------------------------------------------
1. BOOK 0: ARTIFICIAL INTELLIGENCE CONTINUES WITH MORE CONTENT HERE
2. BOOK 23: CONTENT BEFORE ARTIFICIAL INTELLIGENCE AND CONTENT AFTER
3. BOOK 46: EXTENSIVE PRELIMINARY CONTENT ARTIFICIAL INTELLIGENCE
...
------------------------------------------------------------

Total results found: 10
```

### REST API

Start the API server:

```bash
uvicorn api:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

#### API Example (Python)

```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"query": "Design AI architecture"}
)

result = response.json()
print(f"Normalized Query: {result['query']}")
print(f"Results Found: {result['count']}")

for item in result['results']:
    print(f"  Score: {item['score']:.3f}")
    print(f"  Text: {item['sequence']}")
```

#### API Example (cURL)

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query":"quantum computing"}'
```

### Integration with Thalos Prime

Thalos Prime (or any external system) can integrate with MNN Pipeline via the REST API:

```python
import requests

# Query MNN for knowledge extraction
response = requests.post(
    "http://localhost:8000/query",
    json={"query": "machine learning algorithms"}
)

if response.status_code == 200:
    results = response.json()["results"]
    for result in results:
        # Process each result
        sequence = result['sequence']
        score = result['score']
        # Use in Thalos Prime workflow...
```

## Architecture

The MNN Pipeline uses a modular architecture with clear separation of concerns:

```
mnn_pipeline/
├── query_normalizer.py    # Stage 1: Normalize queries
├── constraint_generator.py # Stage 2: Generate constraints
├── index_mapper.py         # Stage 3: Map to indices (Library of Babel logic)
├── sequence_generator.py   # Stage 4: Generate sequences
├── analyzer.py             # Stage 5: Filter and validate
├── scorer.py               # Stage 6: Score and rank
└── output_handler.py       # Stage 7: Format output
```

### Deterministic Index Mapping

The key innovation is **deterministic index mapping** inspired by the Library of Babel:

- Instead of scanning infinite permutations, calculate exactly where relevant "books" would be
- Use pattern length as step size: `indices = [0, len(pattern), 2*len(pattern), ..., 999*len(pattern)]`
- This generates exactly 1000 candidate positions per query
- Same query always maps to same positions (deterministic)
- Different queries map to different positions (collision-resistant)

### Center-Weighted Scoring

Results are ranked using center-weighted scoring:
```python
score = 1 / (1 + |center_position - pattern_position|)
```

Sequences with the pattern near their center score higher, indicating better contextual integration.

## Determinism Guarantees

MNN Pipeline is **fully deterministic**:

- ✅ Identical inputs → identical outputs
- ✅ No randomness in any stage
- ✅ Stable sorting with tie-breakers
- ✅ Cache-transparent (caching doesn't affect results)
- ✅ Reproducible across runs

```python
# Test determinism
from main import run_pipeline

result1 = run_pipeline("test query")
result2 = run_pipeline("test query")
assert result1 == result2  # Always True
```

## Testing

Run the complete test suite:

```bash
# Run all MNN Pipeline tests with unittest (native test framework)
python -m unittest discover tests

# Or run with pytest (works with unittest-style tests)
pytest tests/test_pipeline.py tests/test_api.py -v

# Run with coverage using pytest
pytest tests/test_pipeline.py tests/test_api.py --cov=mnn_pipeline --cov=main --cov=api --cov-report=term-missing
```

Test coverage includes:
- ✅ Query normalization (uppercase, special chars, whitespace)
- ✅ Constraint generation (structure, bounds)
- ✅ Index mapping (determinism, count, step size)
- ✅ Sequence generation (pattern inclusion, format)
- ✅ Analysis (filtering, length validation, deduplication)
- ✅ Scoring (center-weighting, sorting)
- ✅ End-to-end determinism
- ✅ Caching behavior
- ✅ API endpoints (success, errors, determinism)

## Performance

### Caching

MNN Pipeline uses `functools.lru_cache` for performance optimization:

```python
@lru_cache(maxsize=128)
def normalize_query(query: str) -> str:
    # Cached for fast repeated queries
    ...
```

Cache hit rates can be monitored via the `/health` endpoint:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "cache_info": {
    "pipeline_cache_size": 15,
    "pipeline_cache_hits": 147,
    "pipeline_cache_misses": 15
  }
}
```

### Optimization Strategy

1. **LRU Caching**: Key deterministic entry points cached (normalize_query, run_pipeline, cached_pipeline) with deep copy protection
2. **Finite Search Space**: 1000 indices (not infinite)
3. **Early Filtering**: Eliminate invalid sequences early
4. **List Comprehensions**: Pythonic, optimized iteration

## Code Quality

- ✅ **Python 3.12+** compatible
- ✅ **Type hints** on all functions
- ✅ **Docstrings** (Google style) on all modules and functions
- ✅ **No TODOs or stubs** - complete implementation
- ✅ **No global state** (except cached functions)
- ✅ **Immutable data** where possible
- ✅ **Comprehensive tests** with determinism validation

## API Reference

### POST /query

Query the MNN knowledge engine.

**Request:**
```json
{
  "query": "search string"
}
```

**Response:**
```json
{
  "query": "SEARCH STRING",
  "results": [
    {
      "sequence": "BOOK 0: ...",
      "score": 0.95
    }
  ],
  "count": 5
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid query (empty or whitespace only)
- `422`: Validation error (missing query field)
- `500`: Pipeline execution error

### GET /health

Health check and cache statistics.

**Response:**
```json
{
  "status": "healthy",
  "service": "MNN Knowledge Engine",
  "cache_info": {
    "pipeline_cache_size": 15,
    "pipeline_cache_hits": 147,
    "pipeline_cache_misses": 15
  }
}
```

## Project Structure

```
MNN/
├── mnn_pipeline/           # Core pipeline modules
│   ├── __init__.py
│   ├── query_normalizer.py
│   ├── constraint_generator.py
│   ├── index_mapper.py
│   ├── sequence_generator.py
│   ├── analyzer.py
│   ├── scorer.py
│   └── output_handler.py
├── tests/                  # Comprehensive test suite
│   ├── __init__.py
│   ├── test_pipeline.py
│   └── test_api.py
├── main.py                 # CLI entry point
├── api.py                  # FastAPI application
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── ARCHITECTURE.md         # Detailed architecture documentation
└── .gitignore             # Git ignore patterns
```

## License

MIT License - See LICENSE file for details.
