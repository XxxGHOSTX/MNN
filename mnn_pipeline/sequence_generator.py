"""
Sequence generation for the Matrix Neural Network pipeline.
"""

from typing import Dict, Iterable, List


def _render_sequence(index: int, pattern: str) -> str:
    """
    Build a deterministic sequence string for a given index and pattern.
    """
    return f"BOOK {index}: ... {pattern} ..."


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
    return [_render_sequence(idx, pattern) for idx in indices]
