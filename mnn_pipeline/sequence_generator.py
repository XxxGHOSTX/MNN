"""
Sequence Generator Module

Generates candidate sequences for each mapped index, ensuring the pattern is embedded
in each sequence. This simulates retrieving "books" from specific positions in the
Library of Babel, but only those that contain the search pattern.

Enhanced with:
- Query class detection for specialized context generation
- Synonym expansion for improved coverage
- Context-aware framing based on query type
"""

from typing import Optional
from .query_classifier import classify_query, get_query_metadata, QueryClass


def generate_sequences(indices: list, constraints: dict, enable_class_detection: bool = True) -> list:
    """
    Generate sequences for each index containing the pattern.
    
    Each sequence is formatted as a "book" entry from a specific index position,
    with the search pattern embedded within contextual text. This ensures:
    - Every sequence contains the pattern (no false negatives)
    - Deterministic generation (same index + pattern = same sequence)
    - Contextual framing for relevance scoring
    - Query-class-specific context when enabled
    
    Sequence format: "BOOK {index}: CONTEXT {pattern} MORE CONTEXT"
    
    The pattern is positioned at a deterministic location based on the index,
    allowing for center-weighted scoring in later stages.
    
    Args:
        indices: List of candidate index positions
        constraints: Dictionary containing:
            - 'pattern' (str): The pattern to embed in sequences
            - 'min_length' (int): Minimum sequence length (unused in generation)
            - 'max_length' (int): Maximum sequence length (unused in generation)
        enable_class_detection: If True, use query classification for specialized
            context generation (default: True)
            
    Returns:
        List of sequence strings, each containing the pattern
        
    Examples:
        >>> generate_sequences([0, 5], {'pattern': 'HELLO', 'min_length': 5, 'max_length': 55})
        ['BOOK 0: HELLO CONTINUES WITH MORE CONTENT HERE', ...]
        
        >>> # With query classification
        >>> generate_sequences([0], {'pattern': 'FUNCTION SORT'}, enable_class_detection=True)
        ['BOOK 0: IMPLEMENTATION OF FUNCTION SORT WITH OPTIMAL COMPLEXITY']
    """
    pattern = constraints['pattern']
    sequences = []
    
    # Detect query class for specialized context generation
    query_metadata = None
    if enable_class_detection:
        query_class, query_metadata = get_query_metadata(pattern)
    
    # Generate a sequence for each index
    for i, idx in enumerate(indices):
        # Create contextual padding to simulate a "book" entry
        # Pattern placement is deterministic based on sequence position
        # Using modulo of loop counter to vary pattern position for diversity
        position_offset = i % 3
        
        # Use query-class-specific context if available
        if query_metadata:
            prefix = query_metadata['context_prefix']
            suffix = query_metadata['context_suffix']
            
            if position_offset == 0:
                # Pattern near beginning
                sequence = f"BOOK {idx}: {pattern} {suffix}"
            elif position_offset == 1:
                # Pattern in middle
                sequence = f"BOOK {idx}: {prefix} {pattern} {suffix}"
            else:
                # Pattern near end
                sequence = f"BOOK {idx}: {prefix} DETAILED ANALYSIS OF {pattern}"
        else:
            # Fallback to generic context
            if position_offset == 0:
                # Pattern near beginning
                sequence = f"BOOK {idx}: {pattern} CONTINUES WITH MORE CONTENT HERE"
            elif position_offset == 1:
                # Pattern in middle
                sequence = f"BOOK {idx}: CONTENT BEFORE {pattern} AND CONTENT AFTER"
            else:
                # Pattern near end
                sequence = f"BOOK {idx}: EXTENSIVE PRELIMINARY CONTENT {pattern}"
        
        sequences.append(sequence)
    
    return sequences


def generate_sequences_with_candidates_limit(
    indices: list, 
    constraints: dict, 
    max_candidates: int = 1000,
    enable_class_detection: bool = True
) -> list:
    """
    Generate sequences with a configurable limit on candidates.
    
    For large queries or performance-critical scenarios, this limits the number
    of candidate sequences generated. Useful for preventing resource exhaustion
    on queries that would otherwise generate excessive candidates.
    
    Args:
        indices: List of candidate index positions
        constraints: Dictionary containing pattern and length constraints
        max_candidates: Maximum number of sequences to generate (default: 1000)
        enable_class_detection: If True, use query classification (default: True)
        
    Returns:
        List of sequence strings (up to max_candidates)
        
    Examples:
        >>> indices = list(range(10000))  # Very large index list
        >>> sequences = generate_sequences_with_candidates_limit(
        ...     indices, {'pattern': 'TEST'}, max_candidates=100
        ... )
        >>> len(sequences)
        100
    """
    # Limit indices to max_candidates
    limited_indices = indices[:max_candidates]
    
    # Generate sequences with limited indices
    return generate_sequences(limited_indices, constraints, enable_class_detection)


def generate_diverse_sequences(
    indices: list,
    constraints: dict,
    diversity_factor: int = 5
) -> list:
    """
    Generate sequences with enhanced diversity.
    
    Instead of using all consecutive indices, sample indices at regular intervals
    to maximize diversity in pattern placement and context.
    
    Args:
        indices: List of candidate index positions
        constraints: Dictionary containing pattern and length constraints
        diversity_factor: Take every Nth index (default: 5)
            Higher values = more diversity, fewer total sequences
            
    Returns:
        List of diverse sequence strings
        
    Examples:
        >>> indices = list(range(100))
        >>> diverse = generate_diverse_sequences(indices, {'pattern': 'TEST'}, diversity_factor=10)
        >>> len(diverse)
        10
    """
    # Sample indices at regular intervals
    diverse_indices = indices[::diversity_factor]
    
    # Ensure we have at least some results
    if len(diverse_indices) == 0 and len(indices) > 0:
        diverse_indices = [indices[0]]
    
    return generate_sequences(diverse_indices, constraints, enable_class_detection=True)
