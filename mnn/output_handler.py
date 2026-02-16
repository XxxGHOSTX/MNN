"""
Output Handler Module

Handles presentation of results to users.
Provides deterministic output formatting.

Functions:
    output_results: Print top N sequences in numbered format

Author: MNN Engine Contributors
"""


def output_results(sequences: list[str], top_n: int = 10) -> None:
    """
    Output top N sequences in numbered format.
    
    Prints sequences to stdout in stable order, numbered from 1 to N.
    Displays up to top_n sequences (or fewer if list is shorter).
    
    Args:
        sequences: List of sequence strings to output
        top_n: Number of top sequences to display (default: 10)
        
    Returns:
        None (side effect: prints to stdout)
        
    Examples:
        >>> output_results(['ABC', 'DEF', 'GHI'], top_n=2)
        1. ABC
        2. DEF
        >>> output_results(['HELLO'], top_n=10)
        1. HELLO
    """
    # Take top N sequences
    top_sequences = sequences[:top_n]
    
    # Print numbered results
    for idx, sequence in enumerate(top_sequences, start=1):
        print(f"{idx}. {sequence}")
