"""
Deterministic Seed Registry

Manages seeds for deterministic generation and provides ordering utilities.
All operations are fully deterministic to ensure reproducible outputs.

Author: MNN Engine Contributors
"""

import hashlib
from typing import List, Any


def deterministic_hash(data: str) -> int:
    """
    Generate a deterministic hash from a string.
    
    Uses SHA-256 for consistency across platforms and Python versions.
    
    Args:
        data: Input string to hash
        
    Returns:
        Deterministic integer hash value
        
    Examples:
        >>> h1 = deterministic_hash("test")
        >>> h2 = deterministic_hash("test")
        >>> h1 == h2
        True
        >>> deterministic_hash("a") != deterministic_hash("b")
        True
    """
    # Use SHA-256 for deterministic hashing
    hash_bytes = hashlib.sha256(data.encode('utf-8')).digest()
    # Convert first 8 bytes to integer for seed value
    return int.from_bytes(hash_bytes[:8], byteorder='big', signed=False)


class SeedRegistry:
    """
    Registry for deterministic seed management.
    
    Provides methods to generate, store, and retrieve seeds in a deterministic manner.
    All operations maintain ordering guarantees for reproducibility.
    
    Attributes:
        _seeds: Internal storage for registered seeds
        _base_seed: Base seed for derivation
    """
    
    def __init__(self, base_seed: int = 0):
        """
        Initialize the seed registry.
        
        Args:
            base_seed: Base seed for all derived seeds (default: 0)
        """
        self._base_seed = base_seed
        self._seeds: List[int] = []
    
    def register_seed(self, seed: int) -> None:
        """
        Register a seed in the registry.
        
        Args:
            seed: Seed value to register
        """
        self._seeds.append(seed)
    
    def derive_seed(self, context: str) -> int:
        """
        Derive a deterministic seed from a context string.
        
        Combines the base seed with the context to produce a reproducible seed.
        
        Args:
            context: Context string for seed derivation
            
        Returns:
            Derived seed value
            
        Examples:
            >>> registry = SeedRegistry(base_seed=42)
            >>> seed1 = registry.derive_seed("query1")
            >>> seed2 = registry.derive_seed("query1")
            >>> seed1 == seed2
            True
        """
        # Combine base seed and context for deterministic derivation
        combined = f"{self._base_seed}:{context}"
        derived = deterministic_hash(combined)
        self.register_seed(derived)
        return derived
    
    def get_sequence(self, count: int, offset: int = 0) -> List[int]:
        """
        Generate a deterministic sequence of seeds.
        
        Args:
            count: Number of seeds to generate
            offset: Starting offset for the sequence
            
        Returns:
            List of deterministic seed values
            
        Examples:
            >>> registry = SeedRegistry(base_seed=100)
            >>> seq1 = registry.get_sequence(5)
            >>> seq2 = registry.get_sequence(5)
            >>> seq1 == seq2
            True
        """
        seeds = []
        for i in range(count):
            seed = self.derive_seed(f"seq_{offset + i}")
            seeds.append(seed)
        return seeds
    
    def get_all_seeds(self) -> List[int]:
        """
        Retrieve all registered seeds in order.
        
        Returns:
            List of all registered seeds
        """
        return self._seeds.copy()
    
    def clear(self) -> None:
        """Clear all registered seeds."""
        self._seeds.clear()
    
    def __len__(self) -> int:
        """Return the number of registered seeds."""
        return len(self._seeds)
    
    def __repr__(self) -> str:
        """String representation of the registry."""
        return f"SeedRegistry(base_seed={self._base_seed}, count={len(self._seeds)})"


def stable_sort_with_tiebreak(items: List[Any], key_func, tiebreak_func) -> List[Any]:
    """
    Perform stable sorting with deterministic tie-breaking.
    
    When primary sort keys are equal, uses the tiebreak function for deterministic ordering.
    
    Args:
        items: List of items to sort
        key_func: Primary key function for sorting
        tiebreak_func: Tiebreak key function for equal primary keys
        
    Returns:
        Sorted list with deterministic ordering
        
    Examples:
        >>> items = [{'val': 5, 'id': 2}, {'val': 5, 'id': 1}, {'val': 3, 'id': 0}]
        >>> sorted_items = stable_sort_with_tiebreak(
        ...     items,
        ...     key_func=lambda x: x['val'],
        ...     tiebreak_func=lambda x: x['id']
        ... )
        >>> [x['id'] for x in sorted_items]
        [0, 1, 2]
    """
    # Sort with combined key: (primary, tiebreak)
    return sorted(items, key=lambda x: (key_func(x), tiebreak_func(x)))
