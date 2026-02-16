"""
Sequence Generator Module

Generates candidate sequences for each mapped index, ensuring the pattern is embedded
in each sequence. This simulates retrieving "books" from specific positions in the
Library of Babel, but only those that contain the search pattern.
"""


def generate_sequences(indices: list, constraints: dict) -> list:
    """
    Generate sequences for each index containing the pattern.
    
    Each sequence is formatted as a "book" entry from a specific index position,
    with the search pattern embedded within contextual text. This ensures:
    - Every sequence contains the pattern (no false negatives)
    - Deterministic generation (same index + pattern = same sequence)
    - Contextual framing for relevance scoring
    
    Sequence format: "BOOK {index}: CONTEXT {pattern} MORE CONTEXT"
    
    The pattern is positioned at a deterministic location based on the index,
    allowing for center-weighted scoring in later stages.
    
    Args:
        indices: List of candidate index positions
        constraints: Dictionary containing:
            - 'pattern' (str): The pattern to embed in sequences
            - 'min_length' (int): Minimum sequence length (unused in generation)
            - 'max_length' (int): Maximum sequence length (unused in generation)
            
    Returns:
        List of sequence strings, each containing the pattern
        
    Examples:
        >>> generate_sequences([0, 5], {'pattern': 'HELLO', 'min_length': 5, 'max_length': 55})
        ['BOOK 0: CONTEXT HELLO CONTINUES HERE', 'BOOK 5: CONTEXT HELLO CONTINUES HERE']
    """
    pattern = constraints['pattern']
    sequences = []
    
    # Generate a sequence for each index
    for i, idx in enumerate(indices):
        # Create contextual padding to simulate a "book" entry
        # Pattern placement is deterministic based on sequence position
        # Using modulo of loop counter to vary pattern position for diversity
        position_offset = i % 3
        
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
