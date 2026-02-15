"""
Sequence generation for the Matrix Neural Network pipeline.
"""

from functools import lru_cache
from typing import Dict, Iterable, List, Tuple


def _render_sequence(index: int, pattern: str) -> str:
    """
    Build a deterministic sequence string for a given index and pattern.
    """
    return f"BOOK {index}: ... {pattern} ..."


@lru_cache(maxsize=128)
def _generate_sequences_cached(pattern: str, indices: Tuple[int, ...]) -> Tuple[str, ...]:
    """
    Cached helper to build sequences that include the provided pattern.
    """
    return tuple(_render_sequence(idx, pattern) for idx in indices)


def generate_sequences(indices: Iterable[int], constraints: Dict) -> List[str]:
    """
    Generate sequences for each index while including the constraint pattern.

    Args:
        indices: Iterable of candidate indices.
        constraints: Constraint dictionary containing a 'pattern' key.

    Returns:
        List of generated sequence strings.
    """
    pattern = constraints.get("pattern", "")
    indices_tuple = tuple(indices)
    return list(_generate_sequences_cached(pattern, indices_tuple))
