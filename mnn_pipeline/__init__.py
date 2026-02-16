"""
MNN Pipeline Package

A deterministic, constraint-driven knowledge engine inspired by the Library of Babel concept,
transformed into a practical, queryable system that returns only relevant, validated results.

Enhanced with:
- Query classification (code, scientific, mathematical, natural language)
- Synonym expansion for improved query coverage
- Context-aware sequence generation
- Candidate limiting for large-scale queries
"""

from mnn_pipeline.query_normalizer import normalize_query
from mnn_pipeline.constraint_generator import generate_constraints
from mnn_pipeline.index_mapper import map_constraints_to_indices
from mnn_pipeline.sequence_generator import (
    generate_sequences,
    generate_sequences_with_candidates_limit,
    generate_diverse_sequences,
)
from mnn_pipeline.analyzer import analyze_sequences
from mnn_pipeline.scorer import score_and_rank
from mnn_pipeline.output_handler import output_results
from mnn_pipeline.query_classifier import (
    classify_query,
    get_query_metadata,
    QueryClass,
)
from mnn_pipeline.synonym_expander import (
    expand_query_with_synonyms,
    get_related_terms,
    add_synonym,
    get_expansion_preview,
)

__all__ = [
    # Core pipeline functions
    'normalize_query',
    'generate_constraints',
    'map_constraints_to_indices',
    'generate_sequences',
    'analyze_sequences',
    'score_and_rank',
    'output_results',
    
    # Enhanced sequence generation
    'generate_sequences_with_candidates_limit',
    'generate_diverse_sequences',
    
    # Query classification
    'classify_query',
    'get_query_metadata',
    'QueryClass',
    
    # Synonym expansion
    'expand_query_with_synonyms',
    'get_related_terms',
    'add_synonym',
    'get_expansion_preview',
]
