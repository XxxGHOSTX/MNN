"""
Caching utilities for MNN engine.

Provides functools.lru_cache wrapper for pipeline operations.
"""

from functools import lru_cache, wraps
import copy


def pipeline_cache(maxsize: int = 128):
    """
    Create an LRU cache decorator for pipeline functions.
    
    Uses deep copy protection to prevent mutation of cached results.
    
    Args:
        maxsize: Maximum cache size (default: 128).
    
    Returns:
        Cache decorator function.
    
    Examples:
        @pipeline_cache(maxsize=64)
        def my_pipeline(query: str) -> list:
            return process(query)
    """
    def decorator(func):
        # Create the cached version
        cached_func = lru_cache(maxsize=maxsize)(func)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Call cached function
            result = cached_func(*args, **kwargs)
            # Return deep copy to prevent mutation
            return copy.deepcopy(result)
        
        # Expose cache_info and cache_clear
        wrapper.cache_info = cached_func.cache_info
        wrapper.cache_clear = cached_func.cache_clear
        
        return wrapper
    
    return decorator


def clear_cache():
    """
    Clear all pipeline caches.
    
    This is a convenience function for clearing caches.
    Individual cache-decorated functions should expose their own
    cache_clear methods.
    
    Returns:
        None
    """
    # This function serves as a placeholder for global cache clearing
    # Individual functions with @pipeline_cache will have their own cache_clear
    pass
