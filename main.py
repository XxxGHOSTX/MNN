"""
MNN Pipeline Main Entry Point

This module provides the main pipeline execution function and CLI interface
for the Matrix Neural Network (MNN) knowledge engine. It orchestrates all
pipeline stages to produce deterministic, relevant results from user queries.

Enhanced CLI features:
- Interactive mode with session history
- Batch processing from files
- JSON/CSV export formats
- Query history logging
- Progress indicators
"""

import sys
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
    """
    # Stage 1: Normalize query
    pattern = normalize_query(query)
    
    # Validate that normalization didn't result in empty pattern
    if not pattern or not pattern.strip():
        raise ValueError("Query cannot be empty after normalization")
    
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
    
    # Return top N results
    return ranked[:top_n]


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
    Enhanced CLI interface for the MNN pipeline.
    
    Supports multiple modes:
    - Interactive single query (default)
    - Batch processing from file
    - Export to JSON/CSV formats
    - Query history logging
    
    Usage:
        python main.py                          # Interactive mode
        python main.py --query "test"           # Single query
        python main.py --batch queries.txt      # Batch mode
        python main.py --query "test" --json    # Export to JSON
        python main.py --help                   # Show help
        
    Example session:
        $ python main.py
        Enter your query: artificial intelligence
        
        Top 10 Results:
        1. BOOK 0: ARTIFICIAL INTELLIGENCE CONTINUES WITH MORE CONTENT HERE
        2. BOOK 23: CONTENT BEFORE ARTIFICIAL INTELLIGENCE AND CONTENT AFTER
        ...
    """
    import argparse
    import json
    import csv
    import sys
    from datetime import datetime
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="MNN Knowledge Engine - Deterministic query processing",
        epilog="For more information, see README.md"
    )
    
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Query string to process (interactive mode if not provided)'
    )
    
    parser.add_argument(
        '--batch', '-b',
        type=str,
        metavar='FILE',
        help='Process queries from file (one per line)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    
    parser.add_argument(
        '--csv',
        type=str,
        metavar='FILE',
        help='Export results to CSV file'
    )
    
    parser.add_argument(
        '--top-n',
        type=int,
        default=10,
        metavar='N',
        help='Number of top results to return (default: 10)'
    )
    
    parser.add_argument(
        '--log-queries',
        action='store_true',
        help='Log queries and results to query_history.log'
    )
    
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress indicators (useful for piping output)'
    )
    
    args = parser.parse_args()
    
    # Batch mode
    if args.batch:
        process_batch(args.batch, args.top_n, args.json, args.csv, args.log_queries, not args.no_progress)
        return
    
    # Single query mode (command-line argument)
    if args.query:
        process_single_query(
            args.query, 
            args.top_n, 
            args.json, 
            args.csv, 
            args.log_queries,
            show_header=not args.no_progress
        )
        return
    
    # Interactive mode (default)
    interactive_mode(args.top_n, args.log_queries)


def process_single_query(query, top_n=10, json_output=False, csv_file=None, log_queries=False, show_header=True):
    """Process a single query and output results."""
    import json
    import csv
    from datetime import datetime
    
    if show_header:
        print("=" * 60)
        print("MNN Knowledge Engine - Query Interface")
        print("=" * 60)
        print()
        print(f"Processing query: '{query}'")
        print()
    
    # Run pipeline
    results = _execute_pipeline(query, top_n)
    
    # Log if requested
    if log_queries:
        log_query_history(query, results)
    
    # Output based on format
    if json_output:
        output_json(query, results)
    elif csv_file:
        output_csv(csv_file, query, results)
    else:
        if show_header:
            print(f"Top {top_n} Results:")
            print("-" * 60)
        output_results(results)
        if show_header:
            print("-" * 60)
            print()
            print(f"Total results found: {len(results)}")


def process_batch(batch_file, top_n=10, json_output=False, csv_file=None, log_queries=False, show_progress=True):
    """Process multiple queries from a file."""
    import json
    from datetime import datetime
    
    try:
        with open(batch_file, 'r') as f:
            queries = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: File '{batch_file}' not found", file=sys.stderr)
        return
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return
    
    if not queries:
        print("Error: No queries found in file", file=sys.stderr)
        return
    
    print(f"Processing {len(queries)} queries from {batch_file}...")
    print()
    
    all_results = []
    
    for i, query in enumerate(queries, 1):
        if show_progress:
            print(f"[{i}/{len(queries)}] Processing: {query[:50]}{'...' if len(query) > 50 else ''}")
        
        try:
            results = _execute_pipeline(query, top_n)
            all_results.append({
                'query': query,
                'results': results,
                'count': len(results)
            })
            
            if log_queries:
                log_query_history(query, results)
                
        except Exception as e:
            print(f"  Error processing query: {e}", file=sys.stderr)
            all_results.append({
                'query': query,
                'error': str(e),
                'results': [],
                'count': 0
            })
    
    # Output results
    if json_output:
        print(json.dumps({
            'batch_file': batch_file,
            'total_queries': len(queries),
            'timestamp': datetime.now().isoformat(),
            'queries': all_results
        }, indent=2))
    elif csv_file:
        output_batch_csv(csv_file, all_results)
    else:
        print()
        print("=" * 60)
        print("Batch Processing Complete")
        print("=" * 60)
        print(f"Total queries processed: {len(queries)}")
        print(f"Successful: {sum(1 for r in all_results if 'error' not in r)}")
        print(f"Failed: {sum(1 for r in all_results if 'error' in r)}")


def interactive_mode(top_n=10, log_queries=False):
    """Interactive session with multiple queries."""
    import sys
    
    print("=" * 60)
    print("MNN Knowledge Engine - Interactive Mode")
    print("=" * 60)
    print()
    print("Enter queries (one per line). Type 'quit' or press Ctrl+C to exit.")
    print("Commands:")
    print("  quit, exit     - Exit the program")
    print("  history        - Show query history for this session")
    print("  cache          - Show cache statistics")
    print("  clear          - Clear screen")
    print()
    
    session_history = []
    
    while True:
        try:
            query = input("Query> ").strip()
            
            if not query:
                continue
            
            # Handle commands
            if query.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
            
            if query.lower() == 'history':
                print()
                print("Session History:")
                for i, (q, count) in enumerate(session_history, 1):
                    print(f"  {i}. {q} ({count} results)")
                print()
                continue
            
            if query.lower() == 'cache':
                cache_info = _cached_execute_pipeline.cache_info()
                print()
                print("Cache Statistics:")
                print(f"  Hits: {cache_info.hits}")
                print(f"  Misses: {cache_info.misses}")
                print(f"  Size: {cache_info.currsize} / {cache_info.maxsize}")
                print(f"  Hit rate: {cache_info.hits / (cache_info.hits + cache_info.misses) * 100:.1f}%" if cache_info.hits + cache_info.misses > 0 else "  No queries yet")
                print()
                continue
            
            if query.lower() == 'clear':
                import os
                os.system('clear' if os.name != 'nt' else 'cls')
                continue
            
            # Process query
            print()
            results = _execute_pipeline(query, top_n)
            
            print(f"Top {top_n} Results:")
            print("-" * 60)
            output_results(results)
            print("-" * 60)
            print(f"Found {len(results)} results")
            print()
            
            # Update session history
            session_history.append((query, len(results)))
            
            # Log if requested
            if log_queries:
                log_query_history(query, results)
                
        except KeyboardInterrupt:
            print()
            print("Goodbye!")
            break
        except EOFError:
            print()
            print("Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            print()


def output_json(query, results):
    """Output results in JSON format."""
    import json
    from datetime import datetime
    
    output = {
        'query': query,
        'timestamp': datetime.now().isoformat(),
        'count': len(results),
        'results': results
    }
    
    print(json.dumps(output, indent=2))


def output_csv(filename, query, results):
    """Output results to CSV file."""
    import csv
    
    try:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['query', 'rank', 'sequence', 'score'])
            
            for i, result in enumerate(results, 1):
                writer.writerow([
                    query,
                    i,
                    result['sequence'],
                    result['score']
                ])
        
        print(f"Results exported to {filename}")
        
    except Exception as e:
        print(f"Error writing CSV file: {e}", file=sys.stderr)


def output_batch_csv(filename, all_results):
    """Output batch results to CSV file."""
    import csv
    
    try:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['query', 'rank', 'sequence', 'score', 'error'])
            
            for item in all_results:
                query = item['query']
                
                if 'error' in item:
                    writer.writerow([query, '', '', '', item['error']])
                else:
                    for i, result in enumerate(item['results'], 1):
                        writer.writerow([
                            query,
                            i,
                            result['sequence'],
                            result['score'],
                            ''
                        ])
        
        print(f"Batch results exported to {filename}")
        
    except Exception as e:
        print(f"Error writing CSV file: {e}", file=sys.stderr)


def log_query_history(query, results):
    """Log query and results to history file."""
    import json
    from datetime import datetime
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'query': query,
        'result_count': len(results),
        'top_score': results[0]['score'] if results else 0
    }
    
    try:
        with open('query_history.log', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        print(f"Warning: Could not write to query history: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
