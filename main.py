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


@lru_cache(maxsize=128)
def run_pipeline(query: str) -> List[Dict[str, Any]]:
    """
    Execute the complete MNN pipeline for a given query.
    
    Pipeline stages:
    1. Query Normalization: Clean and standardize input
    2. Constraint Generation: Create deterministic constraints
    3. Index Mapping: Map to candidate "book" positions
    4. Sequence Generation: Generate sequences at each index
    5. Analysis/Filtering: Validate and filter sequences
    6. Scoring/Ranking: Rank by relevance (center-weighted)
    7. Return top 10 results
    
    The pipeline is fully deterministic: identical inputs always produce
    identical outputs. This is enforced through:
    - Deterministic constraint generation
    - Fixed index mapping algorithm
    - Stable sorting with tie-breakers
    - LRU caching for performance
    
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
    """
    # Stage 1: Normalize query
    pattern = normalize_query(query)
    
    # Stage 2: Generate constraints
    constraints = generate_constraints(pattern)
    
    # Stage 3: Map constraints to indices
    indices = map_constraints_to_indices(constraints)
    
    # Stage 4: Generate candidate sequences
    candidates = generate_sequences(indices, constraints)
    
    # Stage 5: Analyze and filter sequences
    valid = analyze_sequences(candidates, constraints)
    
    # Stage 6: Score and rank sequences
    ranked = score_and_rank(valid, constraints)
    
    # Return top 10 results
    return ranked[:10]


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
