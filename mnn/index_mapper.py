"""
Index Mapping Module

Maps constraints to candidate indices for sequence generation.
Uses LRU caching for performance while maintaining determinism.

Functions:
    map_constraints_to_indices: Generate candidate indices from constraints

Author: MNN Engine Contributors
"""

from functools import lru_cache


@lru_cache(maxsize=128)
def _cached_index_range(pattern_length: int) -> tuple[int, ...]:
    """
    Generate cached index range based on pattern length.
    
    Uses tuple for hashability in lru_cache. This helper ensures
    deterministic index generation with performance caching.
    
    Args:
        pattern_length: Length of the pattern string
        
    Returns:
        Tuple of candidate indices
    """
    step = max(1, pattern_length)
    indices = list(range(0, 1000, step))
    return tuple(indices)


def map_constraints_to_indices(constraints: dict) -> list[int]:
    """
    Map constraints to candidate indices for sequence generation.
    
    Generates a list of candidate indices based on the pattern length.
    Indices are generated as range(0, 1000, step) where step = max(1, len(pattern)).
    Uses an LRU-cached helper to ensure deterministic and efficient computation.
    
    Args:
        constraints: Dictionary with 'pattern' key (str)
        
    Returns:
        List of candidate indices (integers)
        
    Raises:
        ValueError: If constraints dict is missing 'pattern' key
        KeyError: If 'pattern' key is not present in constraints
        
    Examples:
        >>> map_constraints_to_indices({'pattern': 'HELLO'})[:5]
        [0, 5, 10, 15, 20]
        >>> map_constraints_to_indices({'pattern': 'HI'})[:5]
        [0, 2, 4, 6, 8]
        >>> len(map_constraints_to_indices({'pattern': 'A'}))
        1000
    """
    pattern = constraints['pattern']
    pattern_length = len(pattern)
    
    # Use cached helper for deterministic and efficient index generation
    indices_tuple = _cached_index_range(pattern_length)
    
    # Convert back to list for downstream processing
    return list(indices_tuple)
