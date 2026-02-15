"""
Constraint generation for the Matrix Neural Network pipeline.
"""

from functools import lru_cache


@lru_cache(maxsize=128)
def generate_constraints(normalized_query: str) -> dict:
    """
    Generate deterministic constraints from a normalized query.

    Args:
        normalized_query: Normalized query string.

    Returns:
        Dictionary containing pattern, min_length, and max_length values.
    """
    pattern = normalized_query or ""
    min_length = len(pattern)
    max_length = min_length + 50
    return {
        "pattern": pattern,
        "min_length": min_length,
        "max_length": max_length,
    }

