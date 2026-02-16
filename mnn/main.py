"""
MNN CLI Interface

Command-line interface for the MNN deterministic pipeline.
Provides interactive query processing with formatted output.

Usage:
    python -m mnn.main
    
    Or:
    python /path/to/mnn/main.py
    
    Then enter queries when prompted. Press Ctrl+C or Ctrl+D to exit.

Example:
    $ python -m mnn.main
    MNN Deterministic Pipeline - CLI
    =================================
    Enter your query (or Ctrl+C to exit): test query
    
    Top 10 Results:
    ---------------
    1. XXXXtestXXXX
    2. XXtestXXXXXX
    ...

Author: MNN Engine Contributors
"""

from .pipeline import run_pipeline
from .output_handler import output_results


def main() -> None:
    """
    Main CLI entrypoint for MNN pipeline.
    
    Reads queries from stdin, processes through pipeline,
    and outputs results to stdout.
    
    Returns:
        None
    """
    print("MNN Deterministic Pipeline - CLI")
    print("=" * 35)
    print()
    
    try:
        while True:
            try:
                # Read query from user
                query = input("Enter your query (or Ctrl+C to exit): ").strip()
                
                if not query:
                    print("Error: Query cannot be empty\n")
                    continue
                
                # Run pipeline
                ranked_results = run_pipeline(query)
                
                # Extract sequences for output
                sequences = [result['sequence'] for result in ranked_results]
                
                # Display results
                print(f"\nTop {min(10, len(sequences))} Results:")
                print("-" * 35)
                output_results(sequences, top_n=10)
                print()
                
            except ValueError as e:
                print(f"Error: {e}\n")
            except EOFError:
                # Ctrl+D pressed
                print("\nExiting...")
                break
                
    except KeyboardInterrupt:
        # Ctrl+C pressed
        print("\nExiting...")


if __name__ == "__main__":
    main()
