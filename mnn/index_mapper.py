"""
Index mapping module for MNN engine.

Maps constraints to deterministic indices for sequence generation.
"""

from functools import lru_cache


@lru_cache(maxsize=128)
def _compute_indices_for_pattern(pattern: str) -> tuple[int, ...]:
    """
    Compute deterministic indices for a pattern (cached helper).
    
    Args:
        pattern: The pattern string.
    
    Returns:
        Tuple of deterministic indices.
    """
    step = max(1, len(pattern))
    return tuple(range(0, 1000, step))


def map_constraints_to_indices(constraints: dict) -> list[int]:
    """
    Map constraints to deterministic indices.
    
    Generates indices in range(0, 1000, max(1, len(pattern))).
    Uses lru_cache for efficiency.
    
    Args:
        constraints: Dictionary containing 'pattern' key.
    
    Returns:
        List of deterministic integer indices.
    
    Examples:
        >>> map_constraints_to_indices({'pattern': 'TEST'})
        [0, 4, 8, 12, 16, ...]
    """
    pattern = constraints['pattern']
    return list(_compute_indices_for_pattern(pattern))
