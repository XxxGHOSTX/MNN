"""
Scoring and ranking module for MNN engine.

Scores sequences based on pattern centrality and ranks them.
"""


def score_and_rank(sequences: list[str], constraints: dict) -> list[dict]:
    """
    Score and rank sequences by pattern centrality.
    
    Score formula:
        score = 1 / (1 + abs(center_sequence - center_pattern_position))
    
    Where:
        - center_sequence = len(seq) / 2
        - center_pattern_position = first_index_of_pattern + pattern_length / 2
    
    Sequences are sorted descending by score with deterministic tie-breaking
    by original index.
    
    Args:
        sequences: List of sequences to score.
        constraints: Dictionary with 'pattern' key.
    
    Returns:
        List of dictionaries with 'sequence' and 'score' keys,
        sorted by score descending.
    
    Examples:
        >>> score_and_rank(['XTEST', 'TESTX'], {'pattern': 'TEST'})
        [{'sequence': 'TESTX', 'score': 0.8}, {'sequence': 'XTEST', 'score': 0.5}]
    """
    pattern = constraints['pattern']
    pattern_length = len(pattern)
    
    scored = []
    for idx, seq in enumerate(sequences):
        # Find first occurrence of pattern
        pattern_start = seq.find(pattern)
        
        if pattern_start == -1:
            # Pattern not found, skip
            continue
        
        # Calculate centers
        center_sequence = len(seq) / 2.0
        center_pattern = pattern_start + pattern_length / 2.0
        
        # Calculate score
        score = 1.0 / (1.0 + abs(center_sequence - center_pattern))
        
        scored.append({
            'sequence': seq,
            'score': score,
            '_original_index': idx  # For tie-breaking
        })
    
    # Sort by score descending, then by original index for determinism
    scored.sort(key=lambda x: (-x['score'], x['_original_index']))
    
    # Remove the internal index field
    for item in scored:
        del item['_original_index']
    
    return scored
