"""
Sequence analysis module for MNN engine.

Filters sequences based on pattern matching and length constraints.
"""


def analyze_sequences(sequences: list[str], constraints: dict) -> list[str]:
    """
    Analyze and filter sequences based on constraints.
    
    Keeps sequences that:
    1. Contain the pattern
    2. Have length within min_length <= len(seq) <= max_length + 100
    
    Args:
        sequences: List of sequences to analyze.
        constraints: Dictionary with 'pattern', 'min_length', 'max_length'.
    
    Returns:
        Filtered list of sequences meeting all constraints.
    
    Examples:
        >>> analyze_sequences(['XTEST', 'NOPE', 'TESTX'], 
        ...                   {'pattern': 'TEST', 'min_length': 4, 'max_length': 54})
        ['XTEST', 'TESTX']
    """
    pattern = constraints['pattern']
    min_length = constraints['min_length']
    max_length = constraints['max_length'] + 100
    
    filtered = []
    for seq in sequences:
        # Check pattern presence
        if pattern not in seq:
            continue
        
        # Check length constraints
        seq_len = len(seq)
        if min_length <= seq_len <= max_length:
            filtered.append(seq)
    
    return filtered
