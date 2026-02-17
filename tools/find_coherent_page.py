#!/usr/bin/env python3
"""
Babel Siphon CLI Tool - Find Coherent Pages

Command-line interface for the SMT-Arbiter "Babel Siphon" pipeline.
Provides deterministic, SMT-validated outputs for text and code queries.

Usage:
    python tools/find_coherent_page.py "your query here"
    python tools/find_coherent_page.py "write a python function" --seed 42 --max-candidates 100
    python tools/find_coherent_page.py "find text with hello" --top-n 5

Author: MNN Engine Contributors
"""

import sys
import argparse
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mnn.babel_siphon import BabelSiphonPipeline


def format_result(result: dict, verbose: bool = False) -> str:
    """
    Format a pipeline result for display.
    
    Args:
        result: Pipeline result dictionary
        verbose: Include detailed statistics
        
    Returns:
        Formatted string
    """
    output_lines = []
    
    # Header
    output_lines.append("=" * 70)
    output_lines.append("BABEL SIPHON PIPELINE RESULTS")
    output_lines.append("=" * 70)
    output_lines.append("")
    
    # Status
    status = result.get('status', 'unknown')
    output_lines.append(f"Status: {status.upper()}")
    output_lines.append("")
    
    # If no valid candidates found
    if status == 'no_valid_candidates':
        output_lines.append("No candidates satisfied the constraints.")
        output_lines.append("")
        output_lines.append("Message:")
        output_lines.append(f"  {result.get('message', 'Unknown error')}")
        output_lines.append("")
        
        if verbose and 'schema' in result:
            output_lines.append("Constraint Schema:")
            output_lines.append(json.dumps(result['schema'], indent=2))
            output_lines.append("")
        
        if verbose and 'statistics' in result:
            output_lines.append("Statistics:")
            for key, value in result['statistics'].items():
                output_lines.append(f"  {key}: {value}")
            output_lines.append("")
        
        return '\n'.join(output_lines)
    
    # Success case - show results
    results = result.get('results', [])
    output_lines.append(f"Found {len(results)} validated result(s)")
    output_lines.append("")
    
    # Display each result
    for i, item in enumerate(results, start=1):
        output_lines.append("-" * 70)
        output_lines.append(f"Result #{item.get('rank', i)} (Score: {item.get('score', 0):.2f})")
        output_lines.append("-" * 70)
        output_lines.append("")
        output_lines.append(item.get('content', ''))
        output_lines.append("")
        
        if verbose and 'metadata' in item:
            output_lines.append("Metadata:")
            for key, value in item['metadata'].items():
                output_lines.append(f"  {key}: {value}")
            output_lines.append("")
    
    # Statistics (if verbose)
    if verbose and 'statistics' in result:
        output_lines.append("=" * 70)
        output_lines.append("PIPELINE STATISTICS")
        output_lines.append("=" * 70)
        output_lines.append("")
        for key, value in result['statistics'].items():
            output_lines.append(f"  {key}: {value}")
        output_lines.append("")
    
    # Schema (if verbose)
    if verbose and 'schema' in result:
        output_lines.append("=" * 70)
        output_lines.append("CONSTRAINT SCHEMA")
        output_lines.append("=" * 70)
        output_lines.append("")
        output_lines.append(json.dumps(result['schema'], indent=2))
        output_lines.append("")
    
    return '\n'.join(output_lines)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Find coherent, SMT-validated pages using Babel Siphon pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find text pages with "hello world"
  %(prog)s "find text with hello world"
  
  # Find Python code
  %(prog)s "write a python function" --seed 42
  
  # Get more results with verbose output
  %(prog)s "algorithm example" --top-n 10 --verbose
  
  # Use custom seed for reproducibility
  %(prog)s "test query" --seed 12345 --max-candidates 100
        """
    )
    
    parser.add_argument(
        'query',
        type=str,
        help='Query string to process'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=0,
        help='Base seed for deterministic generation (default: 0)'
    )
    
    parser.add_argument(
        '--max-candidates',
        type=int,
        default=50,
        help='Maximum number of candidates to generate (default: 50)'
    )
    
    parser.add_argument(
        '--top-n',
        type=int,
        default=10,
        help='Number of top results to return (default: 10)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed statistics and schema'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    args = parser.parse_args()
    
    # Run pipeline
    try:
        pipeline = BabelSiphonPipeline(
            base_seed=args.seed,
            max_candidates=args.max_candidates,
            top_n=args.top_n
        )
        
        result = pipeline.run(args.query)
        
        # Output results
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(format_result(result, verbose=args.verbose))
        
        # Exit with appropriate code
        if result['status'] == 'success':
            sys.exit(0)
        else:
            sys.exit(1)
    
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()
