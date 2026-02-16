"""
Constraint Generation Module

Generates constraints from normalized queries for downstream processing.
Produces deterministic constraint dictionaries with validation.

Functions:
    generate_constraints: Extract constraints from normalized query

Author: MNN Engine Contributors
"""


def generate_constraints(normalized_query: str) -> dict:
    """
    Generate constraints from a normalized query.
    
    Produces a constraint dictionary containing:
    - pattern: The normalized query pattern
    - min_length: Minimum sequence length (length of pattern)
    - max_length: Maximum sequence length (length of pattern + 50)
    
    Args:
        normalized_query: Normalized query string (non-empty)
        
    Returns:
        Dictionary with keys: pattern (str), min_length (int), max_length (int)
        
    Raises:
        ValueError: If normalized_query is empty or invalid
        
    Examples:
        >>> generate_constraints("HELLO")
        {'pattern': 'HELLO', 'min_length': 5, 'max_length': 55}
        >>> generate_constraints("TEST 123")
        {'pattern': 'TEST 123', 'min_length': 8, 'max_length': 58}
        >>> generate_constraints("")
        Traceback (most recent call last):
            ...
        ValueError: Pattern cannot be empty
    """
    # Validate non-empty pattern
    if not normalized_query:
        raise ValueError("Pattern cannot be empty")
    
    pattern = normalized_query
    pattern_length = len(pattern)
    
    # Generate constraints
    constraints = {
        'pattern': pattern,
        'min_length': pattern_length,
        'max_length': pattern_length + 50
    }
    
    return constraints
