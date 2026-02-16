# THALOS Quick Start Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/XxxGHOSTX/MNN.git
cd MNN

# Install dependencies
pip install -r requirements.txt
```

## Running the Complete Operational Sequence

The fastest way to see THALOS in action:

```bash
python examples/operational_sequence.py
```

This demonstrates the complete workflow:
1. PRNG initialization with https://libraryofbabel.info logic
2. Semantic Sieve filtering (99.999% noise removal)
3. Matrix Neural Network training with encrypted weights
4. THALOS chatbot deployment with PostgreSQL buffer

## Running Tests

```bash
# Run all tests
python -m unittest discover tests

# Run specific component tests
python -m unittest tests.test_thalos          # Linear algebra stack
python -m unittest tests.test_permutation     # Permutation engine
python -m unittest tests.test_encryption      # Weight encryption
python -m unittest tests.test_mind            # LLM handler
python -m unittest tests.test_buffer          # Relational buffer
```

## Basic Usage Examples

### 1. THALOS Linear Algebra

```python
from src.thalos.linear_algebra import ThalosMatrix

# Create matrices
m1 = ThalosMatrix([[1, 2], [3, 4]])
m2 = ThalosMatrix([[5, 6], [7, 8]])

# Operations
result = m1.matmul(m2)
activated = m1.apply_activation("relu")
transposed = m1.transpose()
```

### 2. Permutation Engine (3-Stage Process)

```python
from src.permutation.engine import PermutationEngine

# Initialize with Library-inspired seed
engine = PermutationEngine(seed=42)

# Complete 3-stage refinement
output = engine.process(
    dimensions=10,
    cardinality=29,  # 29-character set
    refinement_iterations=3
)

print(f"Refined output shape: {output.shape}")
```

### 3. Geometric Character Embeddings

```python
from src.mind.llm_handler import GeometricCharacterEmbedding

# Initialize embeddings (29 characters: a-z + space, comma, period)
embedding = GeometricCharacterEmbedding(embedding_dim=512)

# Encode text to manifold vertices
text = "hello world"
embeddings = embedding.encode(text)

# Calculate relational distances
dist = embedding.relational_distance('a', 'z')
print(f"Distance between 'a' and 'z': {dist:.4f}")
```

### 4. Semantic Sieve (Noise Filtering)

```python
from src.mind.llm_handler import SemanticSieve

# Initialize sieve (filters 99.999% of noise)
sieve = SemanticSieve(noise_threshold=0.99999)

# Filter text
texts = ["the quick brown fox", "xqzjkwlmnp"]

for text in texts:
    is_valid, confidence = sieve.filter(text)
    print(f"Text: '{text}' | Valid: {is_valid} | Confidence: {confidence:.4f}")
```

### 5. Weight Encryption

```python
from src.encryption.weight_encryptor import WeightEncryptor
import numpy as np

# Initialize encryptor (hardware-bound)
encryptor = WeightEncryptor()

# Encrypt weights
weights = np.random.randn(100, 100)
encrypted = encryptor.encrypt_weights(weights)

# Rotate key (during training)
encryptor.rotate_key()

# Decrypt
decrypted = encryptor.decrypt_weights(encrypted)
print(f"Encryption verified: {np.allclose(weights, decrypted)}")
```

### 6. Mind (LLM) Handler

```python
from src.mind.llm_handler import MindLLMHandler

# Initialize Mind with 200M+ parameter support
mind = MindLLMHandler(embedding_dim=512, hidden_dim=2048)

# Generate text
prompt = "artificial intelligence"
response = mind.generate(prompt, max_length=50, temperature=0.8)

# Evaluate confidence
confidence = mind.evaluate_confidence(response)
print(f"Generated: {response}")
print(f"Confidence: {confidence:.4f}")
```

### 7. PostgreSQL Relational Buffer

```python
from src.buffer.relational_buffer import RelationalBuffer

# Connect to buffer
buffer = RelationalBuffer()
buffer.connect()

# Store successful resolution
buffer.store_successful_resolution(
    query="hello world",
    response="generated response",
    confidence=0.95
)

# Store void log (knowledge gap)
buffer.store_void_log(
    query="unknown query",
    failure_reason="Low confidence",
    confidence=0.1,
    void_type="noise"
)

# Analyze knowledge gaps
analysis = buffer.analyze_knowledge_gaps()
print(f"Success rate: {analysis['success_rate']*100:.2f}%")
print(f"Void types: {analysis['void_type_distribution']}")
```

## Complete Integration Example

```python
from src.permutation.engine import PermutationEngine
from src.mind.llm_handler import MindLLMHandler, SemanticSieve
from src.encryption.weight_encryptor import WeightEncryptor
from src.buffer.relational_buffer import RelationalBuffer

# 1. Initialize components
engine = PermutationEngine(seed=42)
sieve = SemanticSieve(noise_threshold=0.99999)
mind = MindLLMHandler(embedding_dim=512, hidden_dim=2048)
encryptor = WeightEncryptor()
buffer = RelationalBuffer()
buffer.connect()

# 2. Generate and filter permutations
permutations = engine.process(dimensions=10, cardinality=29)

# 3. Process query
query = "test query"
response = mind.generate(query, max_length=50)
confidence = mind.evaluate_confidence(response)

# 4. Encrypt weights
import numpy as np
encrypted_weights = encryptor.encrypt_weights(mind.parameters['hidden_layer_1'])

# 5. Store in buffer
if confidence > 0.5:
    buffer.store_successful_resolution(query, response, confidence)
else:
    buffer.store_void_log(query, "Low confidence", confidence, "noise")

print("THALOS pipeline complete!")
```

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    THALOS SYSTEM                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Permutation Engine (https://libraryofbabel.info)      │    │
│  │  • Stage 1: Permutation Generation             │    │
│  │  • Stage 2: Mathematical Refinement            │    │
│  │  • Stage 3: Conceptual Filtering               │    │
│  └────────────────────────────────────────────────┘    │
│                        ↓                                 │
│  ┌────────────────────────────────────────────────┐    │
│  │  Semantic Sieve (99.999% noise filtering)      │    │
│  └────────────────────────────────────────────────┘    │
│                        ↓                                 │
│  ┌────────────────────────────────────────────────┐    │
│  │  Geometric Character Embeddings                 │    │
│  │  (29-char set: a-z + space, comma, period)     │    │
│  └────────────────────────────────────────────────┘    │
│                        ↓                                 │
│  ┌────────────────────────────────────────────────┐    │
│  │  Matrix Neural Network (200M+ params)          │    │
│  │  • THALOS Linear Algebra Stack                 │    │
│  │  • Weight Encryption (hardware-bound)          │    │
│  └────────────────────────────────────────────────┘    │
│                        ↓                                 │
│  ┌────────────────────────────────────────────────┐    │
│  │  PostgreSQL Relational Buffer                   │    │
│  │  • manifold_coordinates (successes)            │    │
│  │  • void_logs (knowledge gaps)                  │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Key Concepts

- **29-Character Set**: a-z + space + comma + period
- **Semantic Sieve**: Filters 99.999% of random permutations
- **Geometric Embeddings**: Characters as manifold vertices
- **Weight Encryption**: Hardware-bound with rotating keys
- **Void Space**: Tracked knowledge gaps in PostgreSQL

## Documentation

- [README.md](../README.md) - Full documentation
- [TECHNICAL.md](../docs/TECHNICAL.md) - Technical deep dive
- [operational_sequence.py](../examples/operational_sequence.py) - Complete workflow

## Next Steps

1. Run the operational sequence example
2. Explore individual components with the usage examples
3. Review the technical documentation for implementation details
4. Run tests to understand component behavior
5. Integrate THALOS into your own projects

## Support

For issues, questions, or contributions, visit:
https://github.com/XxxGHOSTX/MNN
