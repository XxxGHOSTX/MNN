"""
Sequence Generation Module

Generates sequences by embedding patterns at deterministic positions.
Supports concurrent generation with ordering preservation.

Functions:
    generate_sequences: Generate sequences from indices and constraints

Author: MNN Engine Contributors
"""

from concurrent.futures import ThreadPoolExecutor
from typing import List


def _generate_single_sequence(index: int, pattern: str, max_length: int) -> str:
    """
    Generate a single sequence with pattern embedded at deterministic position.
    
    Args:
        index: Candidate index for position calculation
        pattern: Pattern string to embed
        max_length: Maximum allowed length
        
    Returns:
        Generated sequence string
    """
    # Calculate deterministic position for pattern embedding
    pos = index % (len(pattern) + 1)
    
    # Create base filler (deterministic characters derived from pattern)
    # Use 'X' as primary filler for simplicity and determinism
    filler_char = 'X'
    
    # Calculate target length (ensure it doesn't exceed max_length + 100)
    target_length = min(len(pattern) + 20, max_length + 100)
    
    # Ensure we have enough space for the pattern
    if pos + len(pattern) > target_length:
        # Adjust position to fit pattern within target length
        pos = max(0, target_length - len(pattern))
    
    # Build sequence: prefix + pattern + suffix
    prefix = filler_char * pos
    suffix = filler_char * (target_length - pos - len(pattern))
    
    sequence = prefix + pattern + suffix
    
    # Ensure length constraint
    if len(sequence) > max_length + 100:
        sequence = sequence[:max_length + 100]
    
    return sequence


def generate_sequences(indices: list[int], constraints: dict) -> list[str]:
    """
    Generate sequences by embedding pattern at deterministic positions.
    
    For each index in the sorted list of indices:
    1. Calculate position: pos = index % (len(pattern) + 1)
    2. Embed pattern at calculated position within filler string
    3. Ensure sequence length <= max_length + 100
    
    Uses ThreadPoolExecutor for performance but maintains deterministic
    ordering by sorting indices first and preserving order in results.
    
    Args:
        indices: List of candidate indices
        constraints: Dictionary with 'pattern' and 'max_length' keys
        
    Returns:
        List of generated sequences in deterministic order
        
    Examples:
        >>> constraints = {'pattern': 'ABC', 'max_length': 53}
        >>> seqs = generate_sequences([0, 4, 8], constraints)
        >>> len(seqs)
        3
        >>> all('ABC' in seq for seq in seqs)
        True
    """
    pattern = constraints['pattern']
    max_length = constraints['max_length']
    
    # Sort indices to ensure deterministic ordering
    sorted_indices = sorted(indices)
    
    # Generate sequences with ThreadPoolExecutor (ordering preserved by sorted input)
    with ThreadPoolExecutor() as executor:
        sequences = list(executor.map(
            lambda idx: _generate_single_sequence(idx, pattern, max_length),
            sorted_indices
        ))
    
    return sequences
