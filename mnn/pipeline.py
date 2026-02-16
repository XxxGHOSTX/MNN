"""
Pipeline Orchestration Module

Orchestrates the end-to-end MNN pipeline with caching.
Coordinates all stages from query normalization to ranked results.

Functions:
    run_pipeline: Execute complete pipeline for a query

Author: MNN Engine Contributors
"""

from typing import List, Dict

from .query_normalizer import normalize_query
from .constraint_generator import generate_constraints
from .index_mapper import map_constraints_to_indices
from .sequence_generator import generate_sequences
from .analyzer import analyze_sequences
from .scorer import score_and_rank
from .cache import cached_pipeline


@cached_pipeline(maxsize=128)
def run_pipeline(query: str) -> list[dict]:
    """
    Execute the complete MNN pipeline for a query.
    
    Pipeline stages:
    1. Normalize query
    2. Generate constraints from normalized query
    3. Map constraints to candidate indices
    4. Generate sequences from indices
    5. Analyze and filter sequences
    6. Score and rank sequences
    
    Results are cached based on the input query string for performance.
    The cache is deterministic and provides deep-copy protection.
    
    Args:
        query: Input query string
        
    Returns:
        List of dictionaries with 'sequence' and 'score' keys,
        sorted by score in descending order
        
    Raises:
        ValueError: If query normalization produces empty string
        
    Examples:
        >>> results = run_pipeline("test query")
        >>> isinstance(results, list)
        True
        >>> all('sequence' in r and 'score' in r for r in results)
        True
        
        >>> # Cached results are identical
        >>> results1 = run_pipeline("hello")
        >>> results2 = run_pipeline("hello")
        >>> results1 == results2
        True
    """
    # Stage 1: Normalize query
    normalized_query = normalize_query(query)
    
    # Stage 2: Generate constraints
    constraints = generate_constraints(normalized_query)
    
    # Stage 3: Map to indices
    indices = map_constraints_to_indices(constraints)
    
    # Stage 4: Generate sequences
    sequences = generate_sequences(indices, constraints)
    
    # Stage 5: Analyze and filter
    filtered_sequences = analyze_sequences(sequences, constraints)
    
    # Stage 6: Score and rank
    ranked_results = score_and_rank(filtered_sequences, constraints)
    
    return ranked_results
