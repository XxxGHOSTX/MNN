"""
Sequence Scoring and Ranking Module

Scores sequences based on pattern centering and provides deterministic ranking.
Implements stable sorting with tie-breaking for reproducible results.

Functions:
    score_and_rank: Score and rank sequences by pattern position

Author: MNN Engine Contributors
"""


def score_and_rank(sequences: list[str], constraints: dict) -> list[dict]:
    """
    Score and rank sequences based on pattern centering.
    
    Scoring algorithm:
    1. Calculate sequence center: len(sequence) / 2
    2. Find first occurrence of pattern
    3. Calculate pattern center: first_index + len(pattern) / 2
    4. Score = 1 / (1 + abs(sequence_center - pattern_center))
    
    Higher scores indicate pattern is more centered in the sequence.
    
    Deterministic tie-breaking: Uses stable sort with original index preserved.
    Results are sorted in descending order by score.
    
    Args:
        sequences: List of sequence strings to score
        constraints: Dictionary with 'pattern' key
        
    Returns:
        List of dictionaries with 'sequence' and 'score' keys,
        sorted by score descending with deterministic tie-breaking
        
    Examples:
        >>> constraints = {'pattern': 'ABC'}
        >>> seqs = ['XABCX', 'XXABCXX', 'ABCXXXX']
        >>> results = score_and_rank(seqs, constraints)
        >>> len(results)
        3
        >>> all('sequence' in r and 'score' in r for r in results)
        True
        >>> results[0]['score'] >= results[1]['score'] >= results[2]['score']
        True
    """
    pattern = constraints['pattern']
    pattern_length = len(pattern)
    
    scored_sequences = []
    
    for original_index, sequence in enumerate(sequences):
        # Calculate sequence center
        sequence_center = len(sequence) / 2.0
        
        # Find first occurrence of pattern
        pattern_index = sequence.find(pattern)
        
        if pattern_index == -1:
            # Pattern not found (should not happen if analyze_sequences was called)
            # Assign lowest score
            score = 0.0
        else:
            # Calculate pattern center
            pattern_center = pattern_index + (pattern_length / 2.0)
            
            # Calculate score (higher = more centered)
            distance = abs(sequence_center - pattern_center)
            score = 1.0 / (1.0 + distance)
        
        scored_sequences.append({
            'sequence': sequence,
            'score': score,
            '_original_index': original_index  # For deterministic tie-breaking
        })
    
    # Sort by score descending, then by original index for deterministic tie-breaking
    scored_sequences.sort(key=lambda x: (-x['score'], x['_original_index']))
    
    # Remove internal _original_index from results
    results = [
        {'sequence': item['sequence'], 'score': item['score']}
        for item in scored_sequences
    ]
    
    return results
