# SMT-Arbiter "Babel Siphon" Pipeline

A deterministic, SMT-validated content generation pipeline that ensures all outputs satisfy formal constraints. Never emits unvalidated noise.

## Overview

The Babel Siphon pipeline implements a rigorous constraint-validation approach to content generation:

1. **Formalization**: Converts user queries into formal Constraint Compilation Schemas (CCS)
2. **Generation**: Produces candidates from a deterministic semantic lattice
3. **Validation**: Validates candidates via Z3 SMT solver
4. **Repair**: Attempts deterministic repair of failed candidates
5. **Ranking**: Scores and ranks validated candidates
6. **Output**: Returns only SMT-validated results or clean "none found" messages

## Key Features

### ✓ Full Determinism
- Same query + same seed = identical outputs on every run
- No randomness without explicit seeding
- Deterministic tie-breaking in all rankings
- Ready for "Determinism Jail" CI validation

### ✓ SMT Validation
- Length bounds checking
- Required token containment
- Character set validation
- Code domain invariants (brace balance, keyword presence)
- Breach detection with repair coordinates

### ✓ Clean Error Handling
- Never emits unvalidated noise
- Returns explicit "no_valid_candidates" status for unsatisfiable constraints
- Provides detailed statistics on validation/repair attempts

### ✓ Type Safety
- Pydantic models for all IR schemas
- Python 3.12 compatible
- Type hints throughout

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

Key dependencies:
- `z3-solver==4.13.4.0` - SMT constraint solving
- `pydantic==2.7.1` - Type-safe data models
- `numpy==1.26.4` - Numerical operations

### CLI Usage

```bash
# Find text pages
python tools/find_coherent_page.py "hello world"

# Find Python code
python tools/find_coherent_page.py "write a python function" --seed 42

# More results with verbose output
python tools/find_coherent_page.py "algorithm example" --top-n 10 --verbose

# Custom parameters
python tools/find_coherent_page.py "test query" \
  --seed 12345 \
  --max-candidates 100 \
  --top-n 5
```

### Python API

```python
from mnn.babel_siphon import BabelSiphonPipeline

# Create pipeline
pipeline = BabelSiphonPipeline(
    base_seed=42,
    max_candidates=50,
    max_repair_attempts=3,
    top_n=10
)

# Run query
result = pipeline.run("find text with hello world")

if result['status'] == 'success':
    for item in result['results']:
        print(f"Rank {item['rank']}: {item['content']}")
        print(f"Score: {item['score']}")
else:
    print(f"No valid candidates: {result['message']}")
```

### Convenience Function

```python
from mnn.babel_siphon import run_babel_siphon_pipeline

result = run_babel_siphon_pipeline(
    "hello world",
    base_seed=42,
    max_candidates=50,
    top_n=10
)
```

## Architecture

### Module Structure

```
mnn/
├── babel_siphon.py          # Main pipeline orchestration
├── core/
│   ├── seed_registry.py     # Deterministic seed management
│   └── semantic_lattice.py  # Candidate generation
├── ir/
│   └── models.py            # Typed IR models (ConstraintSchema, Candidate, BreachCoordinates)
├── formalization/
│   └── ccs.py               # Query → CCS formalization
├── solver/
│   └── smt_solver.py        # Z3-based SMT validation
└── scoring/
    └── ranker.py            # Deterministic scoring and ranking

tools/
└── find_coherent_page.py    # CLI interface
```

### Pipeline Stages

1. **Formalization** (`mnn.formalization.ccs`)
   - Detects domain (text, code, language-specific)
   - Extracts required tokens
   - Infers length bounds
   - Determines character set
   - Builds code invariants

2. **Seed Derivation** (`mnn.core.seed_registry`)
   - Derives deterministic seed from query
   - Ensures reproducibility

3. **Candidate Generation** (`mnn.core.semantic_lattice`)
   - Generates candidates from constraint schema
   - Domain-aware generation (text vs. code)
   - Incorporates required tokens
   - Deterministic from seed

4. **SMT Validation** (`mnn.solver.smt_solver`)
   - Validates against constraint schema
   - Checks: length, tokens, charset, code invariants
   - Emits `BreachCoordinates` on failure

5. **Repair** (`mnn.solver.smt_solver`)
   - Attempts deterministic repair using breach hints
   - Strategies: padding, truncation, token insertion, char replacement
   - Re-validates after repair

6. **Scoring & Ranking** (`mnn.scoring.ranker`)
   - Scores based on: token coverage, length optimality, structural density
   - Deterministic tie-breaking
   - Returns top-N results

## IR Models

### ConstraintSchema

Formal constraint specification derived from queries.

```python
from mnn.ir.models import ConstraintSchema

schema = ConstraintSchema(
    required_tokens=['hello', 'world'],
    domain_hints=['text'],
    min_length=10,
    max_length=100,
    charset='printable',
    code_invariants={}
)
```

### Candidate

Generated content candidate.

```python
from mnn.ir.models import Candidate

candidate = Candidate(
    content='hello world example',
    seed=42,
    generation_step=0,
    metadata={'target_length': 50}
)
```

### BreachCoordinates

Constraint violation details for repair.

```python
from mnn.ir.models import BreachCoordinates

breach = BreachCoordinates(
    violated_constraints=['length_too_short'],
    missing_tokens=['hello'],
    length_violation='too_short',
    repair_hints=['pad_to_20', 'insert_hello']
)

if breach.is_repairable():
    # Attempt repair
    pass
```

## Testing

Run the test suite:

```bash
# Babel Siphon tests only
python -m pytest tests/test_babel_siphon.py -v

# All tests
python -m pytest

# With coverage
python -m pytest --cov=mnn --cov-report=html
```

Test categories:
- IR model validation
- Deterministic seed management
- Query formalization
- Candidate generation
- SMT validation and repair
- Scoring and ranking
- Complete pipeline execution

## Determinism Guarantees

The pipeline provides **strict determinism**:

- ✓ Same query + same seed → identical outputs
- ✓ No uncontrolled randomness
- ✓ Stable sorting with tie-breaking
- ✓ Deterministic hash functions (SHA-256)
- ✓ Reproducible across runs and platforms

### Determinism Testing

```python
from mnn.babel_siphon import BabelSiphonPipeline

pipeline = BabelSiphonPipeline(base_seed=42)
result1 = pipeline.run('test')
result2 = pipeline.run('test')

assert result1 == result2  # Always passes
```

### Determinism Jail CI

Ready for CI validation with determinism constraints:

```yaml
# Example CI check
- name: Test Determinism
  run: |
    python -c "
    from mnn.babel_siphon import run_babel_siphon_pipeline
    r1 = run_babel_siphon_pipeline('test', base_seed=42)
    r2 = run_babel_siphon_pipeline('test', base_seed=42)
    assert r1 == r2, 'Non-deterministic behavior detected!'
    "
```

## Security

### Dependency Pinning

All dependencies are pinned to exact versions in `requirements.txt`:
- `z3-solver==4.13.4.0`
- `pydantic==2.7.1`
- `numpy==1.26.4`

### SBOM Generation

Generate Software Bill of Materials:

```bash
pip install pip-audit
pip-audit --format json > sbom.json
```

### Security Best Practices

- No arbitrary code execution
- Input validation via Pydantic
- Constraint bounds to prevent resource exhaustion
- Character set validation to prevent injection
- No external network calls in pipeline

## Observability

### Structured Logging Placeholders

The pipeline includes hooks for structured logging:

```python
# Example integration
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pipeline = BabelSiphonPipeline(base_seed=42)
result = pipeline.run('query')

# Log statistics
logger.info('Pipeline execution', extra={
    'query': 'query',
    'status': result['status'],
    'statistics': result['statistics']
})
```

### Metrics Collection

Pipeline results include detailed statistics:

```json
{
  "statistics": {
    "candidates_generated": 50,
    "candidates_validated": 12,
    "candidates_failed": 38,
    "repair_attempts": 45,
    "repair_successes": 8
  }
}
```

### Recommended Metrics

Track these metrics in production:
- `babel_siphon_queries_total` - Total queries processed
- `babel_siphon_validation_rate` - Ratio of validated candidates
- `babel_siphon_repair_success_rate` - Ratio of successful repairs
- `babel_siphon_duration_seconds` - Query processing time

## FastAPI Integration

Example FastAPI wrapper:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mnn.babel_siphon import BabelSiphonPipeline

app = FastAPI()
pipeline = BabelSiphonPipeline(base_seed=42)

class QueryRequest(BaseModel):
    query: str
    seed: int = 42
    max_candidates: int = 50
    top_n: int = 10

@app.post("/babel-siphon")
async def query_pipeline(req: QueryRequest):
    pipeline = BabelSiphonPipeline(
        base_seed=req.seed,
        max_candidates=req.max_candidates,
        top_n=req.top_n
    )
    result = pipeline.run(req.query)
    
    if result['status'] == 'no_valid_candidates':
        raise HTTPException(status_code=404, detail=result['message'])
    
    return result
```

## Performance Considerations

### Tuning Parameters

- `max_candidates`: Higher values increase quality but cost more validation time
- `max_repair_attempts`: Balance between repair success rate and latency
- `top_n`: Limit result set for faster response

### Recommended Settings

**Development:**
```python
BabelSiphonPipeline(
    base_seed=42,
    max_candidates=20,
    max_repair_attempts=2,
    top_n=5
)
```

**Production:**
```python
BabelSiphonPipeline(
    base_seed=0,  # Vary by deployment
    max_candidates=50,
    max_repair_attempts=3,
    top_n=10
)
```

**High Quality:**
```python
BabelSiphonPipeline(
    base_seed=0,
    max_candidates=100,
    max_repair_attempts=5,
    top_n=20
)
```

## License

See LICENSE file for details.

## Contributing

See CONTRIBUTING.md for contribution guidelines.

## Authors

MNN Engine Contributors
