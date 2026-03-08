"""
MNN: Deterministic Matrix Neural Network Engine

A fully deterministic pipeline for query processing, constraint generation,
sequence generation, analysis, scoring, and ranking. All operations are 
side-effect free (except defined I/O) and produce identical results for 
identical inputs.

Key Features:
- Deterministic query normalization and constraint generation
- Index-based sequence generation with pattern embedding
- Sequence analysis and filtering based on constraints
- Scoring and ranking with deterministic tie-breaking
- LRU caching for performance with cache coherence guarantees
- Type-safe with comprehensive type hints (Python 3.12+)
- Thread-safe where applicable with ordering preservation

Architecture:
    Query → Normalize → Constraints → Indices → Sequences → 
    Analyze → Score/Rank → Results

Modules:
    query_normalizer: Input query normalization
    constraint_generator: Constraint extraction from queries
    index_mapper: Constraint-to-index mapping
    sequence_generator: Deterministic sequence generation
    analyzer: Sequence filtering and analysis
    scorer: Scoring and ranking with deterministic ordering
    output_handler: Result presentation
    cache: Deterministic LRU caching
    pipeline: End-to-end orchestration
    main: CLI entrypoint
    api: REST API interface

Author: MNN Engine Contributors
License: MIT
"""

__version__ = "1.0.0"
__all__ = [
    "query_normalizer",
    "constraint_generator",
    "index_mapper",
    "sequence_generator",
    "analyzer",
    "scorer",
    "output_handler",
    "cache",
    "pipeline",
    "main",
    "api",
    "deterministic",
]
