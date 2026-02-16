"""
Query normalization module for MNN engine.

Provides deterministic query normalization by converting to uppercase,
stripping non-alphanumeric characters (except spaces), and collapsing
whitespace.
"""

import re


def normalize_query(query: str) -> str:
    """
    Normalize a query string deterministically.
    
    Normalization steps:
    1. Convert to uppercase
    2. Strip non-alphanumeric characters (keep spaces)
    3. Collapse multiple whitespace to single space
    4. Strip leading/trailing whitespace
    
    Args:
        query: The input query string to normalize.
    
    Returns:
        Normalized query string.
    
    Raises:
        ValueError: If the normalized query is empty.
    
    Examples:
        >>> normalize_query("Hello World!")
        'HELLO WORLD'
        >>> normalize_query("  test   query  ")
        'TEST QUERY'
    """
    # Convert to uppercase
    normalized = query.upper()
    
    # Keep only alphanumeric and spaces
    normalized = re.sub(r'[^A-Z0-9\s]', '', normalized)
    
    # Collapse whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Strip leading/trailing whitespace
    normalized = normalized.strip()
    
    # Validate non-empty
    if not normalized:
        raise ValueError("Normalized query cannot be empty")
    
    return normalized
