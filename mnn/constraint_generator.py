"""
Constraint generation module for MNN engine.

Generates processing constraints based on normalized queries.
"""


def generate_constraints(normalized_query: str) -> dict:
    """
    Generate constraints for sequence processing.
    
    Creates a constraint dictionary with pattern, min_length, and max_length.
    
    Args:
        normalized_query: The normalized query string (pattern).
    
    Returns:
        Dictionary with keys:
            - pattern: The normalized query
            - min_length: Length of pattern
            - max_length: Length of pattern + 50
    
    Examples:
        >>> generate_constraints("TEST")
        {'pattern': 'TEST', 'min_length': 4, 'max_length': 54}
    """
    pattern_length = len(normalized_query)
    
    return {
        'pattern': normalized_query,
        'min_length': pattern_length,
        'max_length': pattern_length + 50
    }
