"""
Sequence Analysis Module

Analyzes and filters sequences based on constraints.
Provides deterministic filtering with pattern matching.

Functions:
    analyze_sequences: Filter sequences by pattern and length constraints

Author: MNN Engine Contributors
"""


def analyze_sequences(sequences: list[str], constraints: dict) -> list[str]:
    """
    Analyze and filter sequences based on constraints.
    
    Filters sequences that:
    1. Contain the pattern
    2. Satisfy length constraints: min_length <= len(seq) <= max_length + 100
    
    Args:
        sequences: List of sequence strings to analyze
        constraints: Dictionary with 'pattern', 'min_length', 'max_length' keys
        
    Returns:
        List of sequences that pass all filters (preserves input order)
        
    Examples:
        >>> constraints = {
        ...     'pattern': 'ABC',
        ...     'min_length': 3,
        ...     'max_length': 53
        ... }
        >>> seqs = ['XABCX', 'XYZ', 'ABCDEFGHIJ', 'X' * 200]
        >>> analyze_sequences(seqs, constraints)
        ['XABCX', 'ABCDEFGHIJ']
    """
    pattern = constraints['pattern']
    min_length = constraints['min_length']
    max_length = constraints['max_length'] + 100  # Allow up to max_length + 100
    
    filtered_sequences = []
    
    for sequence in sequences:
        # Check if pattern is present
        if pattern not in sequence:
            continue
        
        # Check length constraints
        seq_length = len(sequence)
        if not (min_length <= seq_length <= max_length):
            continue
        
        # Sequence passes all filters
        filtered_sequences.append(sequence)
    
    return filtered_sequences
