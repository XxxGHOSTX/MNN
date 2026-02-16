"""
Constraint Generator Module

Generates deterministic constraints from normalized queries to guide the sequence generation
and filtering process. Constraints include pattern matching, length bounds, and other
validation criteria.
"""


def generate_constraints(normalized_query: str) -> dict:
    """
    Generate deterministic constraints from a normalized query.
    
    Creates a constraints dictionary that specifies:
    - pattern: The exact normalized query string to match
    - min_length: Minimum acceptable sequence length (pattern length)
    - max_length: Maximum acceptable sequence length (pattern length + 50)
    
    These constraints ensure that generated sequences are relevant and within
    reasonable bounds.
    
    Args:
        normalized_query: The normalized query string (uppercase, alphanumeric + spaces)
        
    Returns:
        A dictionary containing:
            - 'pattern' (str): The pattern to search for in sequences
            - 'min_length' (int): Minimum sequence length
            - 'max_length' (int): Maximum sequence length
            
    Examples:
        >>> generate_constraints("HELLO")
        {'pattern': 'HELLO', 'min_length': 5, 'max_length': 55}
        >>> generate_constraints("ARTIFICIAL INTELLIGENCE")
        {'pattern': 'ARTIFICIAL INTELLIGENCE', 'min_length': 23, 'max_length': 73}
    """
    pattern_length = len(normalized_query)
    
    constraints = {
        'pattern': normalized_query,
        'min_length': pattern_length,
        'max_length': pattern_length + 50
    }
    
    return constraints
