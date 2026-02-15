"""
Index mapping utilities for the Matrix Neural Network pipeline.
"""

from functools import lru_cache
from typing import Dict, List


@lru_cache(maxsize=128)
def _indices_for_pattern(pattern: str) -> tuple:
    """
    Cached helper to compute index ranges for a given pattern.
    """
    step = max(len(pattern), 1)
    return tuple(range(0, 1000, step))


def map_constraints_to_indices(constraints: Dict) -> List[int]:
    """
    Deterministically map constraints to candidate indices.

    Args:
        constraints: Constraint dictionary containing a 'pattern' key.

    Returns:
        List of candidate indices derived from the pattern length.
    """
    pattern = constraints.get("pattern", "")
    return list(_indices_for_pattern(pattern))
