"""
Scorer Module

Scores and ranks sequences based on pattern position and relevance.
Uses center-weighted scoring where patterns appearing near the center of a sequence
receive higher scores, indicating greater contextual relevance.
"""


def score_and_rank(sequences: list, constraints: dict) -> list:
    """
    Score sequences based on pattern position and rank them.
    
    Scoring algorithm:
    - Center-weighted: Patterns near the sequence center score higher
    - Formula: score = 1 / (1 + abs(center_position - pattern_position))
    - Higher scores indicate better relevance
    - Stable sorting: Uses original index as tie-breaker
    
    The center-weighted approach is based on the principle that relevant content
    typically places key terms in prominent positions, while noise tends to scatter
    them randomly.
    
    Args:
        sequences: List of valid sequence strings
        constraints: Dictionary containing:
            - 'pattern' (str): The pattern to locate within sequences
            - Other constraint fields (unused in scoring)
            
    Returns:
        List of dictionaries sorted by score (descending), each containing:
            - 'sequence' (str): The sequence text
            - 'score' (float): Relevance score (higher is better)
            
    Examples:
        >>> score_and_rank(
        ...     ['BOOK 0: START HELLO END', 'BOOK 1: HELLO AT START'],
        ...     {'pattern': 'HELLO', 'min_length': 5, 'max_length': 55}
        ... )
        [{'sequence': 'BOOK 0: START HELLO END', 'score': 0.5}, ...]
    """
    pattern = constraints['pattern']
    scored_sequences = []
    
    for idx, sequence in enumerate(sequences):
        # Find pattern position in sequence
        pattern_position = sequence.find(pattern)
        
        if pattern_position == -1:
            # Should not happen if analyzer worked correctly
            continue
        
        # Calculate center of sequence
        center_position = len(sequence) / 2
        
        # Calculate center-weighted score
        # Closer to center = higher score
        distance_from_center = abs(center_position - pattern_position)
        score = 1.0 / (1.0 + distance_from_center)
        
        scored_sequences.append({
            'sequence': sequence,
            'score': score,
            'original_index': idx  # For stable tie-breaking
        })
    
    # Sort by score (descending), then by original index (ascending) for stability
    scored_sequences.sort(key=lambda x: (-x['score'], x['original_index']))
    
    # Remove original_index from final output
    return [
        {'sequence': item['sequence'], 'score': item['score']}
        for item in scored_sequences
    ]
