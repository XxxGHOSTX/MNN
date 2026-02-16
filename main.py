"""
MNN Pipeline Main Entry Point

This module provides the main pipeline execution function and CLI interface
for the Matrix Neural Network (MNN) knowledge engine. It orchestrates all
pipeline stages to produce deterministic, relevant results from user queries.
"""

from functools import lru_cache
from typing import List, Dict, Any

from mnn_pipeline import (
    normalize_query,
    generate_constraints,
    map_constraints_to_indices,
    generate_sequences,
    analyze_sequences,
    score_and_rank,
    output_results,
)
from observability import (
    generate_event_id,
    PipelineLogger,
    CheckpointWriter,
    get_metrics_collector,
)
from config import config


def _execute_pipeline(query: str, top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Execute the complete MNN pipeline for a given query.
    
    Internal function that performs the actual pipeline execution.
    This is called by both the CLI (run_pipeline) and API (cached_pipeline)
    to avoid code duplication.
    
    Pipeline stages:
    1. Query Normalization: Clean and standardize input
    2. Constraint Generation: Create deterministic constraints
    3. Index Mapping: Map to candidate "book" positions
    4. Sequence Generation: Generate sequences at each index
    5. Analysis/Filtering: Validate and filter sequences
    6. Scoring/Ranking: Rank by relevance (center-weighted)
    7. Return top N results
    
    Args:
        query: The user's search query (any string)
        top_n: Number of top results to return (default: 10)
        
    Returns:
        List of top N ranked results, each a dictionary containing:
            - 'sequence' (str): The result sequence
            - 'score' (float): Relevance score
            
    Raises:
        ValueError: If the normalized query is empty
        RuntimeError: If pipeline limits are exceeded
    """
    # Stage 1: Normalize query
    pattern = normalize_query(query)
    
    # Validate that normalization didn't result in empty pattern
    if not pattern or not pattern.strip():
        raise ValueError("Query cannot be empty after normalization")
    
    # Initialize observability
    event_id = generate_event_id(pattern)
    logger = PipelineLogger(event_id, query)
    checkpoint_writer = CheckpointWriter(event_id)
    
    # Stage 2: Generate constraints
    logger.start_stage("constraints")
    constraints = generate_constraints(pattern)
    logger.complete_stage("constraints", data={"pattern_length": len(pattern)})
    checkpoint_writer.write_checkpoint("constraints", constraints)
    
    # Stage 3: Map constraints to indices
    logger.start_stage("indices")
    indices = map_constraints_to_indices(constraints)
    
    # Enforce indices limit
    if len(indices) > config.MAX_INDICES_PER_REQUEST:
        logger.error_stage("indices", f"Indices count {len(indices)} exceeds limit {config.MAX_INDICES_PER_REQUEST}")
        raise RuntimeError(
            f"Indices limit exceeded: {len(indices)} > {config.MAX_INDICES_PER_REQUEST}"
        )
    
    logger.complete_stage("indices", data={"indices_count": len(indices)})
    checkpoint_writer.write_checkpoint("indices", indices[:100])  # Limit checkpoint size
    
    # Stage 4: Generate candidate sequences
    logger.start_stage("generate")
    candidates = generate_sequences(indices, constraints)
    
    # Enforce sequences limit
    if len(candidates) > config.MAX_SEQUENCES_PER_REQUEST:
        logger.error_stage("generate", f"Sequences count {len(candidates)} exceeds limit {config.MAX_SEQUENCES_PER_REQUEST}")
        raise RuntimeError(
            f"Sequences limit exceeded: {len(candidates)} > {config.MAX_SEQUENCES_PER_REQUEST}"
        )
    
    logger.complete_stage("generate", data={"sequences_count": len(candidates)})
    
    # Stage 5: Analyze and filter sequences
    logger.start_stage("analyze")
    valid = analyze_sequences(candidates, constraints)
    logger.complete_stage("analyze", data={"valid_count": len(valid)})
    
    # Stage 6: Score and rank sequences
    logger.start_stage("score")
    ranked = score_and_rank(valid, constraints)
    logger.complete_stage("score", data={"ranked_count": len(ranked)})
    
    # Stage 7: Output preparation
    logger.start_stage("output")
    results = ranked[:top_n]
    logger.complete_stage("output", data={"result_count": len(results)})
    checkpoint_writer.write_checkpoint("results", results)
    
    return results


def _cached_execute_pipeline(query: str, top_n: int) -> List[Dict[str, Any]]:
    """Internal cached pipeline execution. Do not call directly."""
    return _execute_pipeline(query, top_n)

# Apply lru_cache to the internal function
_cached_execute_pipeline = lru_cache(maxsize=128)(_cached_execute_pipeline)


def run_pipeline(query: str) -> List[Dict[str, Any]]:
    """
    Execute the complete MNN pipeline for a given query with caching.
    
    The pipeline is fully deterministic: identical inputs always produce
    identical outputs. This is enforced through:
    - Deterministic constraint generation
    - Fixed index mapping algorithm
    - Stable sorting with tie-breakers
    - LRU caching for performance
    
    Note: Returns a deep copy of cached results to prevent cache corruption from mutations.
    Each call returns a fresh deep copy, so mutations to returned values don't affect
    the cache.
    
    Args:
        query: The user's search query (any string)
        
    Returns:
        List of top 10 ranked results, each a dictionary containing:
            - 'sequence' (str): The result sequence
            - 'score' (float): Relevance score
            
    Examples:
        >>> results = run_pipeline("artificial intelligence")
        >>> len(results)
        10
        >>> results[0]['score'] >= results[1]['score']
        True
        >>> # Determinism test
        >>> run_pipeline("test") == run_pipeline("test")
        True
        >>> # Cache mutation protection
        >>> r1 = run_pipeline("test")
        >>> r1[0]['score'] = 999  # Mutate
        >>> r2 = run_pipeline("test")
        >>> r2[0]['score'] != 999  # Cache protected
        True
    """
    # Get cached result and return a deep copy
    # Deep copy happens on every call, not just on cache miss
    import copy
    return copy.deepcopy(_cached_execute_pipeline(query, 10))


def main():
    """
    CLI interface for the MNN pipeline.
    
    Prompts the user for a query and displays the top 10 results.
    Can be run directly from the command line.
    
    Usage:
        python main.py
        
    Example session:
        $ python main.py
        Enter your query: artificial intelligence
        
        Top 10 Results:
        1. BOOK 0: ARTIFICIAL INTELLIGENCE CONTINUES WITH MORE CONTENT HERE
        2. BOOK 23: CONTENT BEFORE ARTIFICIAL INTELLIGENCE AND CONTENT AFTER
        ...
    """
    print("=" * 60)
    print("MNN Knowledge Engine - Query Interface")
    print("=" * 60)
    print()
    
    # Get query from user
    query = input("Enter your query: ").strip()
    
    if not query:
        print("Error: Query cannot be empty")
        return
    
    print()
    print(f"Processing query: '{query}'")
    print()
    
    # Run pipeline
    results = run_pipeline(query)
    
    # Display results
    print("Top 10 Results:")
    print("-" * 60)
    output_results(results)
    print("-" * 60)
    print()
    print(f"Total results found: {len(results)}")


if __name__ == "__main__":
    main()
