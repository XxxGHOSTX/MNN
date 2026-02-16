"""
Sequence generation module for MNN engine.

Generates deterministic sequences embedding patterns at specific positions.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import List


def generate_sequences(indices: list[int], constraints: dict) -> list[str]:
    """
    Generate deterministic sequences with embedded pattern.
    
    For each index, creates a sequence with:
    - Pattern embedded at position: index % (len(pattern) + 1)
    - Total length <= max_length + 100
    - Deterministic padding characters
    
    Args:
        indices: List of indices for sequence generation.
        constraints: Dictionary with 'pattern' and 'max_length'.
    
    Returns:
        List of generated sequences in deterministic order.
    
    Examples:
        >>> generate_sequences([0, 4], {'pattern': 'AB', 'max_length': 52})
        ['AB...', '..AB...', ...]
    """
    pattern = constraints['pattern']
    max_length = constraints['max_length']
    max_seq_length = max_length + 100
    
    # Sort indices for deterministic processing
    sorted_indices = sorted(indices)
    
    def generate_single_sequence(idx: int) -> tuple[int, str]:
        """Generate a single sequence for an index."""
        pattern_pos = idx % (len(pattern) + 1)
        
        # Calculate sequence length deterministically
        seq_length = min(
            len(pattern) + pattern_pos + (idx % 50) + 10,
            max_seq_length
        )
        
        # Build sequence with pattern at pattern_pos
        sequence = ['X'] * seq_length
        
        # Embed pattern
        for i, char in enumerate(pattern):
            if pattern_pos + i < seq_length:
                sequence[pattern_pos + i] = char
        
        return (idx, ''.join(sequence))
    
    # Use ThreadPoolExecutor but maintain deterministic order
    with ThreadPoolExecutor() as executor:
        # Map indices to sequences
        futures = {executor.submit(generate_single_sequence, idx): idx 
                   for idx in sorted_indices}
        
        # Collect results maintaining original index order
        results = {}
        for future in futures:
            idx, seq = future.result()
            results[idx] = seq
    
    # Return in deterministic order (sorted by index)
    return [results[idx] for idx in sorted_indices]
