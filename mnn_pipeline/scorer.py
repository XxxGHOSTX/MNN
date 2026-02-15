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


def score_and_rank(
    sequences: Iterable[Tuple[int, str]], constraints: Dict
) -> List[Dict[str, float]]:
    """
    Score sequences and return them ranked in descending order with stable tie-breaking
    by index.

    Args:
        sequences: Iterable of (index, sequence) tuples to score.
        constraints: Constraint dictionary containing a 'pattern' key.

    Returns:
        List of dicts with sequence and score, sorted by score then index.
    """
    pattern = constraints.get("pattern", "")
    scored = []
    for index, sequence in sequences:
        score = _score_sequence(sequence, pattern)
        if score == INVALID_SCORE:
            continue
        scored.append((score, index, sequence))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [{"sequence": seq, "score": score} for score, _, seq in scored]
