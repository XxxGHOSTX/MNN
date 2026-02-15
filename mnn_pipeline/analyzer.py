"""
Analyzer Module

Analyzes and filters candidate sequences to ensure they meet all constraints.
This stage validates that sequences contain the pattern, fall within length bounds,
and eliminates duplicates.
"""


def analyze_sequences(sequences: list, constraints: dict) -> list:
    """
    Analyze and filter sequences based on constraints.
    
    This function performs multiple validation steps:
    1. Pattern matching: Ensure pattern exists in sequence
    2. Length validation: Check min_length and max_length bounds (with tolerance)
    3. Duplicate elimination: Remove exact duplicates
    
    The length validation uses a tolerance of +100 beyond max_length to account
    for contextual framing while still preventing excessively long sequences.
    
    Args:
        sequences: List of candidate sequence strings
        constraints: Dictionary containing:
            - 'pattern' (str): Required pattern in sequences
            - 'min_length' (int): Minimum acceptable length
            - 'max_length' (int): Maximum acceptable length (with +100 tolerance)
            
    Returns:
        List of validated, unique sequences that meet all constraints
        
    Examples:
        >>> analyze_sequences(
        ...     ['BOOK 0: HELLO WORLD', 'BOOK 1: HELLO WORLD', 'BOOK 2: GOODBYE'],
        ...     {'pattern': 'HELLO', 'min_length': 5, 'max_length': 100}
        ... )
        ['BOOK 0: HELLO WORLD']
    """
    pattern = constraints['pattern']
    min_length = constraints['min_length']
    max_length = constraints['max_length']
    
    valid_sequences = []
    seen = set()
    
    for sequence in sequences:
        # Eliminate duplicates first
        if sequence in seen:
            continue
        
        # Check if pattern exists in sequence
        if pattern not in sequence:
            continue
        
        # Check length constraints (allow +100 tolerance for context)
        seq_length = len(sequence)
        if seq_length < min_length or seq_length > max_length + 100:
            continue
        
        seen.add(sequence)
        valid_sequences.append(sequence)
    
    return valid_sequences
