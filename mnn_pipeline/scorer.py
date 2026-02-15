"""
Scoring and ranking utilities for the Matrix Neural Network pipeline.
"""

from typing import Dict, Iterable, List, Tuple

INVALID_SCORE = float("-inf")


def _score_sequence(sequence: str, pattern: str) -> float:
    """
    Score a sequence by how centrally its pattern appears.
    """
    if not pattern or pattern not in sequence:
        return INVALID_SCORE

    pattern_start = sequence.index(pattern)
    pattern_center = pattern_start + len(pattern) / 2
    center = len(sequence) / 2
    distance = abs(center - pattern_center)
    return -distance  # Higher when pattern is near the center


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
    scored = []
    for seq in sequences:
        score = _score_sequence(seq, pattern)
        if score == INVALID_SCORE:
            continue
        scored.append((score, seq))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [seq for _, seq in scored]
