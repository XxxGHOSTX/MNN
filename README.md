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
