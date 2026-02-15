"""
Query normalization utilities for the Matrix Neural Network pipeline.
"""

import re
from functools import lru_cache


@lru_cache(maxsize=128)
def normalize_query(query: str) -> str:
    """
    Normalize a user query by uppercasing, stripping non-alphanumeric characters
    (except spaces), and collapsing extra whitespace.

    Args:
        query: Raw user query.

    Returns:
        Cleaned and normalized query string.
    """
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", " ", query or "")
    collapsed = " ".join(cleaned.split())
    return collapsed.upper()

