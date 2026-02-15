"""
Sequence analysis for the Matrix Neural Network pipeline.
"""

import sys
from typing import Dict, Iterable, List, Tuple


def analyze_sequences(
    sequences: Iterable[Tuple[int, str]], constraints: Dict
) -> List[Tuple[int, str]]:
    """
    Filter sequences that satisfy constraint requirements.

    Args:
        sequences: Iterable of (index, sequence) tuples.
        constraints: Constraint dictionary with pattern, min_length, and max_length.

    Returns:
        List of valid sequences that meet constraints.
    """
    pattern = constraints.get("pattern", "")
    min_length = constraints.get("min_length", 0)
    max_length = constraints.get("max_length", sys.maxsize)

    valid = []
    for index, sequence in sequences:
        if pattern not in sequence:
            continue
        if not (min_length <= len(sequence) <= max_length):
            continue
        valid.append((index, sequence))
    return valid
