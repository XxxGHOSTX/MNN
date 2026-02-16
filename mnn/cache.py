"""
Caching Module

Provides deterministic LRU caching for pipeline operations.
Ensures cache coherence and reproducible results.

Functions:
    clear_cache: Clear all cached pipeline results

Author: MNN Engine Contributors
"""

from functools import lru_cache
from typing import Callable, Any
import copy


# Cache for pipeline results (keyed by normalized query)
# We'll implement this as a wrapper around lru_cache
_pipeline_cache_registry: list[Callable] = []


def register_cached_function(func: Callable) -> None:
    """
    Register a function that uses caching for later clearing.
    
    Args:
        func: Function with cache_clear method
    """
    if hasattr(func, 'cache_clear') and func not in _pipeline_cache_registry:
        _pipeline_cache_registry.append(func)


def clear_cache() -> None:
    """
    Clear all registered caches.
    
    This function clears the LRU cache for all registered pipeline functions,
    ensuring fresh computation on next call. Useful for testing and when
    memory management is required.
    
    Returns:
        None
        
    Examples:
        >>> clear_cache()  # Clears all pipeline caches
    """
    for func in _pipeline_cache_registry:
        if hasattr(func, 'cache_clear'):
            func.cache_clear()


def cached_pipeline(maxsize: int = 128):
    """
    Decorator for caching pipeline functions with deep copy protection.
    
    This decorator provides LRU caching while ensuring that mutable return
    values (like dicts and lists) are deep-copied before being returned,
    preventing cache corruption from external mutations.
    
    Args:
        maxsize: Maximum cache size (default: 128)
        
    Returns:
        Decorator function
        
    Examples:
        >>> @cached_pipeline(maxsize=64)
        ... def my_pipeline(query: str) -> list[dict]:
        ...     return [{'result': 'data'}]
    """
    def decorator(func: Callable) -> Callable:
        # Create the cached version
        cached_func = lru_cache(maxsize=maxsize)(func)
        
        # Register for clearing
        register_cached_function(cached_func)
        
        # Wrapper that deep copies results
        def wrapper(*args, **kwargs) -> Any:
            result = cached_func(*args, **kwargs)
            # Deep copy to prevent cache corruption
            return copy.deepcopy(result)
        
        # Expose cache_clear for manual clearing
        wrapper.cache_clear = cached_func.cache_clear
        wrapper.cache_info = cached_func.cache_info
        
        return wrapper
    
    return decorator
