"""
CLI entrypoint for MNN engine.

Usage:
    python -m mnn.main
    
    Or from the mnn directory:
    python main.py

The CLI will prompt for a query, process it through the MNN pipeline,
and display the top results.

Examples:
    $ python -m mnn.main
    Enter query: hello world
    1. HELLO WORLDXXXXXXX...
    2. XHELLO WORLDXXXXXX...
    ...
"""

from mnn.pipeline import run_pipeline
from mnn.output_handler import output_results


def main() -> None:
    """
    Main CLI entry point.
    
    Reads query from stdin, processes through pipeline, and outputs results.
    
    Returns:
        None
    """
    print("MNN Engine - Matrix Neural Network Query Processor")
    print("=" * 50)
    
    try:
        # Read query from user
        query = input("Enter query: ").strip()
        
        if not query:
            print("Error: Query cannot be empty")
            return
        
        # Run pipeline
        print("\nProcessing...")
        results = run_pipeline(query)
        
        if not results:
            print("No results found.")
            return
        
        # Extract sequences
        sequences = [r['sequence'] for r in results]
        
        # Output top results
        print(f"\nTop {min(10, len(sequences))} results:")
        print("-" * 50)
        output_results(sequences, top_n=10)
        
        print(f"\nTotal results: {len(results)}")
        
    except ValueError as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
