"""
Main pipeline entrypoint for the Matrix Neural Network (MNN).

Example:
    python main.py "find hidden patterns"
"""

import sys
from functools import lru_cache
from typing import List

from mnn_pipeline.analyzer import analyze_sequences
from mnn_pipeline.constraint_generator import generate_constraints
from mnn_pipeline.index_mapper import map_constraints_to_indices
from mnn_pipeline.output_handler import output_results
from mnn_pipeline.query_normalizer import normalize_query
from mnn_pipeline.scorer import score_and_rank
from mnn_pipeline.sequence_generator import generate_sequences


@lru_cache(maxsize=128)
def run_pipeline(query: str) -> List[str]:
    """
    Execute the full deterministic MNN pipeline for a single query.

    Args:
        query: Raw user query string.

    Returns:
        Ranked list of sequences.
    """
    normalized = normalize_query(query)
    constraints = generate_constraints(normalized)
    indices = map_constraints_to_indices(constraints)
    sequences = generate_sequences(indices, constraints)
    valid_sequences = analyze_sequences(sequences, constraints)
    ranked_sequences = score_and_rank(valid_sequences, constraints)
    return ranked_sequences[:10]


def main() -> None:
    """
    Read user input and run the pipeline, outputting the top results.
    """
    if len(sys.argv) < 2:
        query = input("Enter query: ")
    else:
        query = " ".join(sys.argv[1:])

    ranked_sequences = run_pipeline(query)
    output_results(ranked_sequences[:10])


if __name__ == "__main__":
    main()
