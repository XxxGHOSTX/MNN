"""
Metrics Module for MNN Pipeline

Provides lightweight metrics tracking and snapshot endpoint for monitoring
pipeline performance, cache effectiveness, and request patterns.
All metrics are deterministic and contain no PII.
"""

import time
from collections import defaultdict
from typing import Any, Dict, List
from threading import Lock

# Thread-safe metrics storage
_metrics_lock = Lock()
_metrics: Dict[str, Any] = {
    "counters": defaultdict(int),
    "timings": defaultdict(list),
    "cache_stats": {},
    "recent_requests": [],
}

_MAX_RECENT_REQUESTS = 100
_MAX_TIMING_SAMPLES = 1000


def increment_counter(name: str, value: int = 1) -> None:
    """
    Increment a counter metric.
    
    Args:
        name: Counter name (e.g., "queries.total", "queries.errors")
        value: Amount to increment (default: 1)
    """
    with _metrics_lock:
        _metrics["counters"][name] += value


def record_timing(name: str, duration_ms: float) -> None:
    """
    Record a timing measurement.
    
    Args:
        name: Timing name (e.g., "stage.normalize", "pipeline.total")
        duration_ms: Duration in milliseconds
    """
    with _metrics_lock:
        timings = _metrics["timings"][name]
        timings.append(duration_ms)
        
        # Keep only recent samples (ring buffer)
        if len(timings) > _MAX_TIMING_SAMPLES:
            _metrics["timings"][name] = timings[-_MAX_TIMING_SAMPLES:]


def record_request(metadata: Dict[str, Any]) -> None:
    """
    Record metadata for a recent request (no PII).
    
    Args:
        metadata: Request metadata (event_id, query_length, result_count, etc.)
    """
    with _metrics_lock:
        requests = _metrics["recent_requests"]
        requests.append(metadata)
        
        # Keep only recent requests (ring buffer)
        if len(requests) > _MAX_RECENT_REQUESTS:
            _metrics["recent_requests"] = requests[-_MAX_RECENT_REQUESTS:]


def update_cache_stats(cache_name: str, info: Dict[str, Any]) -> None:
    """
    Update cache statistics.
    
    Args:
        cache_name: Name of the cache (e.g., "pipeline_cache", "api_cache")
        info: Cache info dict from lru_cache.cache_info()
    """
    with _metrics_lock:
        _metrics["cache_stats"][cache_name] = {
            "hits": info.get("hits", 0),
            "misses": info.get("misses", 0),
            "size": info.get("currsize", 0),
            "maxsize": info.get("maxsize", 0),
        }


def get_metrics_snapshot() -> Dict[str, Any]:
    """
    Get a snapshot of all current metrics.
    
    Returns:
        Dictionary containing:
        - counters: All counter values
        - timings: Timing statistics (count, min, max, avg, p50, p95, p99)
        - cache_stats: Cache hit rates and sizes
        - recent_requests: Recent request metadata (limited)
        - timestamp: Snapshot timestamp
    """
    import statistics
    
    with _metrics_lock:
        snapshot = {
            "timestamp": time.time(),
            "counters": dict(_metrics["counters"]),
            "timings": {},
            "cache_stats": dict(_metrics["cache_stats"]),
            "recent_requests": list(_metrics["recent_requests"][-20:]),  # Last 20 only
        }
        
        # Calculate timing statistics
        for name, values in _metrics["timings"].items():
            if not values:
                continue
            
            sorted_values = sorted(values)
            snapshot["timings"][name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": statistics.mean(values),
                "p50": sorted_values[len(sorted_values) // 2],
                "p95": sorted_values[int(len(sorted_values) * 0.95)] if len(sorted_values) > 1 else sorted_values[0],
                "p99": sorted_values[int(len(sorted_values) * 0.99)] if len(sorted_values) > 1 else sorted_values[0],
            }
    
    return snapshot


def reset_metrics() -> None:
    """Reset all metrics. Used for testing."""
    with _metrics_lock:
        _metrics["counters"].clear()
        _metrics["timings"].clear()
        _metrics["cache_stats"].clear()
        _metrics["recent_requests"].clear()
