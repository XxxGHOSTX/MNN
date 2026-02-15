"""
Output handling utilities for the Matrix Neural Network pipeline.
"""

from typing import Iterable


def output_results(sequences: Iterable[str]) -> None:
    """
    Print the top sequences in a numbered, newline-separated list.

    Args:
        sequences: Iterable of ranked sequences.
    """
    for idx, sequence in enumerate(sequences):
        if idx >= 10:
            break
        print(f"{idx + 1}. {sequence}")
