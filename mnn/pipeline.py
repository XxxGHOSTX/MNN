"""
Pipeline orchestration module for MNN engine.

Coordinates all processing stages from query normalization to final results.
"""

from mnn.query_normalizer import normalize_query
from mnn.constraint_generator import generate_constraints
from mnn.index_mapper import map_constraints_to_indices
from mnn.sequence_generator import generate_sequences
from mnn.analyzer import analyze_sequences
from mnn.scorer import score_and_rank
from mnn.cache import pipeline_cache


@pipeline_cache(maxsize=128)
def run_pipeline(query: str) -> list[dict]:
    """
    Execute the complete MNN processing pipeline.
    
    Pipeline stages:
    1. Normalize query
    2. Generate constraints
    3. Map constraints to indices
    4. Generate sequences
    5. Analyze sequences
    6. Score and rank sequences
    
    This function is cached for efficiency. Identical queries return
    identical cached results.
    
    Args:
        query: The input query string.
    
    Returns:
        List of dictionaries with 'sequence' and 'score' keys,
        sorted by score descending.
    
    Raises:
        ValueError: If query normalization fails.
    
    Examples:
        >>> results = run_pipeline("test query")
        >>> len(results) > 0
        True
        >>> all('sequence' in r and 'score' in r for r in results)
        True
    """
    # Stage 1: Normalize query
    normalized = normalize_query(query)
    
    # Stage 2: Generate constraints
    constraints = generate_constraints(normalized)
    
    # Stage 3: Map to indices
    indices = map_constraints_to_indices(constraints)
    
    # Stage 4: Generate sequences
    sequences = generate_sequences(indices, constraints)
    
    # Stage 5: Analyze/filter sequences
    filtered = analyze_sequences(sequences, constraints)
    
    # Stage 6: Score and rank
    ranked = score_and_rank(filtered, constraints)
    
    return ranked
