"""
Query Normalization Module

Provides deterministic query normalization with strict validation.
Converts input queries to a canonical form for downstream processing.

Functions:
    normalize_query: Normalize input query to uppercase, alphanumeric form

Author: MNN Engine Contributors
"""

import re


def normalize_query(query: str) -> str:
    """
    Normalize a query string to canonical form.
    
    Normalization steps:
    1. Convert to uppercase
    2. Remove all non-alphanumeric characters except spaces
    3. Collapse multiple whitespace to single space
    4. Strip leading and trailing whitespace
    5. Validate result is non-empty
    
    Args:
        query: Input query string to normalize
        
    Returns:
        Normalized query string in canonical form
        
    Raises:
        ValueError: If normalized query is empty after processing
        
    Examples:
        >>> normalize_query("Hello World!")
        'HELLO WORLD'
        >>> normalize_query("  test   123  ")
        'TEST 123'
        >>> normalize_query("a-b_c@d")
        'ABCD'
        >>> normalize_query("!!!")
        Traceback (most recent call last):
            ...
        ValueError: Normalized query is empty
    """
    # Step 1: Convert to uppercase
    normalized = query.upper()
    
    # Step 2: Remove non-alphanumeric characters except spaces
    normalized = re.sub(r'[^A-Z0-9\s]', '', normalized)
    
    # Step 3: Collapse multiple whitespace to single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Step 4: Strip leading and trailing whitespace
    normalized = normalized.strip()
    
    # Step 5: Validate non-empty
    if not normalized:
        raise ValueError("Normalized query is empty")
    
    return normalized
