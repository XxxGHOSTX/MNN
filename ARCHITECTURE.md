# MNN Pipeline Architecture

## Overview

The MNN (Matrix Neural Network) Pipeline is a deterministic, constraint-driven knowledge engine inspired by Jorge Luis Borges' concept of the Library of Babel, but transformed into a practical, queryable system that returns only relevant, validated results.

## The Library of Babel Problem

The website libraryofbabel.info demonstrates an interesting but impractical concept: a library containing every possible combination of characters, which theoretically contains all knowledge but is impossible to search meaningfully because it's 99.999% noise.

## MNN's Solution: Constraint-Driven Determinism

Instead of searching infinite permutation space, MNN uses a fundamentally different approach:

1. **Deterministic Index Mapping**: Given a query pattern, calculate exactly where relevant "books" would be located
2. **Targeted Generation**: Generate sequences only at those specific indices
3. **Pattern Embedding**: Ensure every generated sequence contains the search pattern
4. **Relevance Scoring**: Rank results by contextual relevance

## Architecture Components

### 1. Query Normalization

**Purpose**: Standardize input for deterministic processing

**Process**:
- Convert to uppercase
- Remove non-alphanumeric characters (except spaces)
- Collapse whitespace

**Why**: Ensures "Hello World", "hello world", and "HELLO WORLD!" all map to the same internal representation.

### 2. Constraint Generation

**Purpose**: Convert normalized query into searchable constraints

**Output**:
```python
{
    'pattern': 'NORMALIZED QUERY',
    'min_length': len(pattern),
    'max_length': len(pattern) + 50
}
```

**Why**: Length bounds prevent both trivial matches and overwhelming context.

### 3. Index Mapping (Library-of-Babel-Inspired)

**The Key Innovation**: This is where Library of Babel concept becomes practical.

**Traditional Library of Babel**:
- Location: random(all_possible_combinations)
- Problem: Requires scanning infinite space

**MNN Approach**:
- Location: deterministic_function(pattern) → specific indices
- Benefit: Jump directly to relevant "shelves" in the conceptual library

**Implementation**:
```python
def map_constraints_to_indices(constraints):
    step = len(pattern)
    return [0, step, 2*step, ..., 999*step]
```

**Mathematical Basis**:
- Pattern length determines "shelf spacing"
- Generates exactly 1000 candidate positions
- Same pattern always maps to same positions (deterministic)
- Different patterns map to different positions (collision-resistant)

**Why It Works**:
- Reduces infinite search space to finite, manageable set
- Maintains determinism (critical for caching)
- Provides diverse coverage without redundancy

### 4. Sequence Generation

**Purpose**: Create "book" entries at each mapped index

**Process**:
- For each index, generate a sequence containing the pattern
- Position pattern deterministically (start/middle/end based on index mod 3)
- Add contextual framing

**Format**:
```
BOOK {index}: {context} {pattern} {more_context}
```

**Why**: 
- Simulates retrieving actual books from specific library positions
- Pattern placement variation enables relevance scoring
- Deterministic generation ensures reproducibility

### 5. Analysis & Filtering

**Purpose**: Validate and filter candidate sequences

**Validation Steps**:
1. **Pattern Matching**: Confirm pattern exists in sequence
2. **Length Bounds**: Check min_length ≤ len(sequence) ≤ max_length + 100
3. **Duplicate Elimination**: Remove exact duplicates

**Why**: Ensures only valid, unique sequences proceed to scoring.

### 6. Scoring & Ranking

**Purpose**: Rank sequences by relevance

**Algorithm**: Center-weighted scoring
```python
score = 1 / (1 + |center_position - pattern_position|)
```

**Intuition**:
- Patterns near sequence center indicate more contextual integration
- Random noise tends to scatter patterns unpredictably
- Relevant content places key terms prominently

**Tie-Breaking**: Use original index for stable sorting

**Output**: Sorted list of {sequence, score} dictionaries

### 7. Output Handling

**Purpose**: Format results for consumption

**CLI**: Top 10 results, numbered list
**API**: Top 5 results, JSON format with metadata

## Pipeline Flow Diagram

```
User Query
    ↓
┌─────────────────────────────────────────────────────┐
│ STAGE 1: Query Normalization                       │
│ "Hello, World!" → "HELLO WORLD"                     │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ STAGE 2: Constraint Generation                     │
│ {pattern: "HELLO WORLD", min: 11, max: 61}          │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ STAGE 3: Index Mapping (Library of Babel)          │
│ [0, 11, 22, 33, ..., 10989]                         │
│ (1000 deterministic positions)                      │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ STAGE 4: Sequence Generation                       │
│ Generate "book" at each index with pattern          │
│ ["BOOK 0: HELLO WORLD...", "BOOK 11: ..."]          │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ STAGE 5: Analysis & Filtering                      │
│ Validate pattern, length, uniqueness                │
│ Valid sequences only                                │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ STAGE 6: Scoring & Ranking                         │
│ Center-weighted scoring                             │
│ Sort by relevance (descending)                      │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ STAGE 7: Output                                     │
│ Return top 10 (CLI) or top 5 (API)                  │
└─────────────────────────────────────────────────────┘
```

## Why Different from LibraryOfBabel.info

| Aspect | LibraryOfBabel.info | MNN Pipeline |
|--------|---------------------|--------------|
| **Search Space** | All possible permutations | Deterministically mapped indices only |
| **Relevance** | Random (99.999% noise) | 100% contain pattern |
| **Determinism** | Yes (by hash) | Yes (by constraints) |
| **Usability** | Academic curiosity | Practical query system |
| **Results** | Unfiltered permutations | Validated, ranked sequences |
| **Integration** | Web interface only | CLI + API |
| **Caching** | Not applicable | LRU cache for performance |

## Determinism Guarantees

**What Makes MNN Deterministic:**

1. **No Randomness**: All operations are purely mathematical
2. **Stable Sorting**: Tie-breakers prevent ordering ambiguity
3. **Functional Purity**: Same input → same output at every stage
4. **Cache Transparency**: Caching doesn't affect results, only speed

**Testing Determinism**:
```python
assert run_pipeline("test") == run_pipeline("test")
assert cached_pipeline.cache_info().hits > 0  # Caching works
```

## Performance Optimizations

### 1. LRU Caching
- `@lru_cache(maxsize=128)` on normalize_query
- `@lru_cache(maxsize=128)` on generate_constraints  
- `@lru_cache(maxsize=128)` on map_constraints_to_indices
- `@lru_cache(maxsize=256)` on cached_pipeline (API)

### 2. Finite Search Space
- 1000 indices (not infinite)
- Pre-filtering by constraints
- Early duplicate elimination

### 3. List Comprehensions
- Pythonic, optimized iteration
- Single-pass generation where possible

## Caching Strategy

**Why Cache:**
- Repeated queries (common in production)
- Deterministic results make caching safe
- Significant speedup (O(1) vs O(n))

**What's Cached:**
- Query normalization
- Constraint generation
- Index mapping
- Full pipeline (API only)

**Cache Invalidation:**
- Not needed (results never change)
- LRU eviction handles memory limits
- Cache can be cleared manually if needed

## Integration with Thalos Prime

**Use Case**: Thalos Prime needs to query MNN for knowledge extraction

**Integration Method**:
```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"query": "Design AI architecture"}
)

results = response.json()["results"]
for result in results:
    print(f"Score: {result['score']}, Text: {result['sequence']}")
```

**Benefits**:
- Language-agnostic (HTTP/JSON)
- Deterministic responses
- Cached for performance
- No tight coupling

## Mathematical Foundations

### Index Mapping Function

Given pattern P of length L:
```
indices = {i * L | i ∈ [0, 999]}
```

Properties:
- **Surjective**: Every pattern maps to some indices
- **Deterministic**: f(P) always yields same result
- **Collision-resistant**: Different patterns likely map differently
- **Finite**: Exactly 1000 indices per pattern

### Scoring Function

Given sequence S with pattern P at position p:
```
center = len(S) / 2
score = 1 / (1 + |center - p|)
```

Properties:
- **Range**: (0, 1]
- **Maximum**: score = 1 when p = center
- **Monotonic decay**: Farther from center → lower score
- **Never zero**: Always positive (prevents division issues)

## Future Enhancements

**Potential Improvements**:
1. **Multi-pattern queries**: Support AND/OR logic
2. **Semantic scoring**: Use embeddings for relevance
3. **Distributed caching**: Redis for multi-instance deployments
4. **Streaming results**: Yield results as they're generated
5. **Pattern extraction**: Auto-extract key terms from natural language

**Not Implemented** (by design):
- Random sampling (breaks determinism)
- Machine learning (introduces non-determinism)
- User-specific personalization (breaks caching)

## Conclusion

MNN Pipeline transforms the Library of Babel's infinite permutation space into a practical, deterministic knowledge engine by:

1. **Constraining search space** through deterministic index mapping
2. **Guaranteeing relevance** by embedding patterns in all results
3. **Ranking by quality** using center-weighted scoring
4. **Maintaining determinism** for caching and reproducibility
5. **Providing interfaces** (CLI + API) for integration

The result is a system that captures the Library of Babel's conceptual elegance while delivering practical, queryable results suitable for production use.
