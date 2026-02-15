"""
Sequence analysis for the Matrix Neural Network pipeline.
"""

from typing import Dict, Iterable, List


def analyze_sequences(
    sequences: Iterable[str], constraints: Dict
) -> List[str]:
    """
    Filter sequences that satisfy constraint requirements.

    Args:
        sequences: Iterable of sequence strings.
        constraints: Constraint dictionary with pattern, min_length, and max_length.

    Returns:
        List of valid sequences that meet constraints.
    """
    pattern = constraints.get("pattern", "")
    min_length = constraints.get("min_length", 0)
    max_length = constraints.get("max_length", 0) + 100

    valid = []
    for sequence in sequences:
        if pattern not in sequence:
            continue
        if not (min_length <= len(sequence) <= max_length):
            continue
        valid.append(sequence)
    return valid
