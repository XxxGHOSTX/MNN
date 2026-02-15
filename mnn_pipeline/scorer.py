"""
Scoring and ranking utilities for the Matrix Neural Network pipeline.
"""

from typing import Dict, Iterable, List, Tuple


def _score_sequence(sequence: str, pattern: str) -> Tuple[float, str]:
    """
    Score a sequence by how centrally its pattern appears.
    """
    if not pattern or pattern not in sequence:
        return (float("-inf"), sequence)

    pattern_start = sequence.index(pattern)
    pattern_center = pattern_start + len(pattern) / 2
    center = len(sequence) / 2
    distance = abs(center - pattern_center)
    score = -distance  # Higher when pattern is near the center
    return (score, sequence)


def score_and_rank(sequences: Iterable[str], constraints: Dict) -> List[str]:
    """
    Score sequences and return them ranked in descending order.

    Args:
        sequences: Iterable of sequences to score.
        constraints: Constraint dictionary containing a 'pattern' key.

    Returns:
        List of sequences sorted by score (highest first).
    """
    pattern = constraints.get("pattern", "")
    scored = [_score_sequence(seq, pattern) for seq in sequences]
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [seq for _, seq in scored]

