"""
MNN Pipeline Main Entry Point

This module provides the main pipeline execution function and CLI interface
for the Matrix Neural Network (MNN) knowledge engine. It orchestrates all
pipeline stages to produce deterministic, relevant results from user queries.
"""

import os
import time
from functools import lru_cache
from typing import List, Dict, Any, Optional

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
    set_event_id,
    get_event_id,
    PipelineTimer,
)
from metrics import (
    increment_counter,
    record_timing,
    record_request,
    update_cache_stats,
)
from checkpoints import CheckpointManager
from guardrails import validate_normalized_query


def _execute_pipeline(
    query: str,
    top_n: int = 10,
    enable_checkpointing: bool = False,
    checkpoint_dir: str = "checkpoints"
) -> Dict[str, Any]:
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
        enable_checkpointing: Whether to save checkpoints (default: False)
        checkpoint_dir: Directory for checkpoints (default: "checkpoints")
        
    Returns:
        Dictionary containing:
            - 'results': List of top N ranked results
            - 'timings': Stage-level timing information
            - 'event_id': Deterministic event ID
            - 'normalized_query': The normalized query
            
    Raises:
        ValueError: If the normalized query is empty
    """
    pipeline_start = time.perf_counter()
    stage_timings = {}
    
    # Stage 1: Normalize query
    with PipelineTimer("normalize") as timer:
        pattern = normalize_query(query)
    stage_timings["normalize_ms"] = (time.perf_counter() - pipeline_start) * 1000
    
    # Generate deterministic event ID from normalized query
    event_id = generate_event_id(pattern)
    set_event_id(event_id)
    
    # Validate that normalization didn't result in empty pattern
    validate_normalized_query(pattern)
    
    # Stage 2: Generate constraints
    stage_start = time.perf_counter()
    with PipelineTimer("constraints"):
        constraints = generate_constraints(pattern)
    stage_timings["constraints_ms"] = (time.perf_counter() - stage_start) * 1000
    
    # Stage 3: Map constraints to indices
    stage_start = time.perf_counter()
    with PipelineTimer("indices"):
        indices = map_constraints_to_indices(constraints)
    stage_timings["indices_ms"] = (time.perf_counter() - stage_start) * 1000
    
    # Stage 4: Generate candidate sequences
    stage_start = time.perf_counter()
    with PipelineTimer("generate"):
        candidates = generate_sequences(indices, constraints)
    stage_timings["generate_ms"] = (time.perf_counter() - stage_start) * 1000
    
    # Stage 5: Analyze and filter sequences
    stage_start = time.perf_counter()
    with PipelineTimer("analyze"):
        valid = analyze_sequences(candidates, constraints)
    stage_timings["analyze_ms"] = (time.perf_counter() - stage_start) * 1000
    
    # Stage 6: Score and rank sequences
    stage_start = time.perf_counter()
    with PipelineTimer("score"):
        ranked = score_and_rank(valid, constraints)
    stage_timings["score_ms"] = (time.perf_counter() - stage_start) * 1000
    
    # Stage 7: Output (select top N)
    stage_start = time.perf_counter()
    with PipelineTimer("output"):
        results = ranked[:top_n]
    stage_timings["output_ms"] = (time.perf_counter() - stage_start) * 1000
    
    # Total pipeline time
    stage_timings["total_ms"] = (time.perf_counter() - pipeline_start) * 1000
    
    # Record metrics
    increment_counter("queries.total")
    increment_counter("queries.success")
    record_timing("pipeline.total", stage_timings["total_ms"])
    for stage_name, duration in stage_timings.items():
        if stage_name != "total_ms":
            record_timing(f"stage.{stage_name.replace('_ms', '')}", duration)
    
    # Save checkpoint if enabled
    if enable_checkpointing:
        checkpoint_mgr = CheckpointManager(checkpoint_dir)
        checkpoint_mgr.save_checkpoint(
            event_id=event_id,
            query=query,
            normalized_query=pattern,
            constraints=constraints,
            indices=indices,
            sequences=candidates[:100],  # Limit stored sequences
            results=results,
            timings=stage_timings,
        )
    
    return {
        "results": results,
        "timings": stage_timings,
        "event_id": event_id,
        "normalized_query": pattern,
    }


def _cached_execute_pipeline(query: str, top_n: int) -> Dict[str, Any]:
    """Internal cached pipeline execution. Do not call directly."""
    return _execute_pipeline(query, top_n, enable_checkpointing=False)

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
    result = copy.deepcopy(_cached_execute_pipeline(query, 10))
    
    # Update cache stats for monitoring
    cache_info = _cached_execute_pipeline.cache_info()
    update_cache_stats("pipeline_cache", {
        "hits": cache_info.hits,
        "misses": cache_info.misses,
        "currsize": cache_info.currsize,
        "maxsize": cache_info.maxsize,
    })
    
    # Return just the results list for backward compatibility
    return result["results"]


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
