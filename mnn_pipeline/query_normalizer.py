"""
Query Normalizer Module

Normalizes user queries to ensure deterministic processing by converting to uppercase,
removing non-alphanumeric characters (except spaces), and stripping extra whitespace.
"""

import re
from functools import lru_cache


@lru_cache(maxsize=128)
def normalize_query(query: str) -> str:
    """
    Normalize a query string for deterministic processing.
    
    This function performs the following transformations:
    1. Convert to uppercase
    2. Remove non-alphanumeric characters except spaces
    3. Strip leading/trailing whitespace
    4. Collapse multiple spaces into single spaces
    
    Args:
        query: The raw query string to normalize
        
    Returns:
        The normalized query string (uppercase, alphanumeric + spaces only)
        
    Examples:
        >>> normalize_query("Hello, World!")
        'HELLO WORLD'
        >>> normalize_query("  test   query  ")
        'TEST QUERY'
        >>> normalize_query("a@b#c$d")
        'ABCD'
    """
    # Convert to uppercase
    normalized = query.upper()
    
    # Remove non-alphanumeric characters except spaces
    normalized = re.sub(r'[^A-Z0-9\s]', '', normalized)
    
    # Strip leading/trailing whitespace and collapse multiple spaces
    normalized = ' '.join(normalized.split())
    
    return normalized
