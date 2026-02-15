"""
Output handling utilities for the Matrix Neural Network pipeline.
"""

from typing import Iterable, Mapping


def output_results(sequences: Iterable[Mapping[str, object]]) -> None:
    """
    Print the top sequences in a numbered, newline-separated list.

    Args:
        sequences: Iterable of ranked sequences.
    """
    for idx, item in enumerate(sequences):
        if idx >= 10:
            break
        sequence = item.get("sequence", "")
        score = item.get("score", None)
        if score is None:
            print(f"{idx + 1}. {sequence}")
        else:
            print(f"{idx + 1}. {sequence} (score={score:.3f})")
