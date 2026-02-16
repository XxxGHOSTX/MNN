"""
Output handling module for MNN engine.

Provides formatted output for query results.
"""


def output_results(sequences: list[str], top_n: int = 10) -> None:
    """
    Output top N sequences in stable numbered format.
    
    Prints sequences numbered 1..N in stable order with no interactive
    or colored output.
    
    Args:
        sequences: List of sequences to output.
        top_n: Number of top sequences to display (default: 10).
    
    Returns:
        None (prints to stdout).
    
    Examples:
        >>> output_results(['SEQ1', 'SEQ2', 'SEQ3'], top_n=2)
        1. SEQ1
        2. SEQ2
    """
    # Limit to top_n
    display_sequences = sequences[:top_n]
    
    # Print numbered sequences
    for i, seq in enumerate(display_sequences, start=1):
        print(f"{i}. {seq}")
