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
def _generate_sequences_cached(
    pattern: str, min_length: int, max_length: int, indices: Tuple[int, ...]
) -> Tuple[Tuple[int, str], ...]:
    """
    Cached helper to build sequences and enforce constraints.
    """
    generated = []
    for idx in indices:
        seq = _render_sequence(idx, pattern)
        if pattern and pattern not in seq:
            continue
        if not (min_length <= len(seq) <= max_length):
            continue
        generated.append((idx, seq))
    return tuple(generated)


def generate_sequences(indices: Iterable[int], constraints: Dict) -> List[Tuple[int, str]]:
    """
    Generate sequences for each index while including the constraint pattern and enforcing
    length constraints.

    Args:
        indices: Iterable of candidate indices.
        constraints: Constraint dictionary containing a 'pattern' key.

    Returns:
        List of (index, sequence) tuples.
    """
    pattern = constraints.get("pattern", "")
    min_length = constraints.get("min_length", 0)
    max_length = constraints.get("max_length", 0)
    indices_tuple = tuple(indices)
    return list(_generate_sequences_cached(pattern, min_length, max_length, indices_tuple))
