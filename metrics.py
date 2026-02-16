"""
Metrics Module

Provides Prometheus-compatible metrics for monitoring MNN API performance.
Tracks query counts, durations, cache performance, and error rates.
"""

import time
from functools import wraps
from typing import Dict, Any, Callable
from collections import defaultdict
from threading import Lock


class MetricsCollector:
    """
    Simple metrics collector for Prometheus-style metrics.
    
    Tracks:
    - Counter: Monotonically increasing values (queries, errors)
    - Histogram: Distribution of values (query duration)
    - Gauge: Current snapshot values (cache size)
    """
    
    def __init__(self):
        """Initialize metrics storage."""
        self._counters = defaultdict(int)
        self._histograms = defaultdict(list)
        self._gauges = {}
        self._lock = Lock()
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """
        Increment a counter metric.
        
        Args:
            name: Metric name (e.g., 'queries_total')
            value: Amount to increment by (default: 1)
            labels: Optional labels for metric dimensions
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """
        Add observation to histogram metric.
        
        Args:
            name: Metric name (e.g., 'query_duration_seconds')
            value: Observed value
            labels: Optional labels for metric dimensions
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """
        Set current value of a gauge metric.
        
        Args:
            name: Metric name (e.g., 'cache_size')
            value: Current value
            labels: Optional labels for metric dimensions
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics in a structured format.
        
        Returns:
            Dictionary containing all metrics with their values
        """
        with self._lock:
            return {
                'counters': dict(self._counters),
                'histograms': {
                    k: {
                        'count': len(v),
                        'sum': sum(v),
                        'min': min(v) if v else 0,
                        'max': max(v) if v else 0,
                        'avg': sum(v) / len(v) if v else 0,
                    }
                    for k, v in self._histograms.items()
                },
                'gauges': dict(self._gauges),
            }
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            String in Prometheus exposition format
        """
        lines = []
        
        with self._lock:
            # Export counters
            for key, value in sorted(self._counters.items()):
                name, labels_str = self._parse_key(key)
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name}{labels_str} {value}")
            
            # Export histograms
            for key, values in sorted(self._histograms.items()):
                name, labels_str = self._parse_key(key)
                if values:
                    count = len(values)
                    total = sum(values)
                    lines.append(f"# TYPE {name} histogram")
                    lines.append(f"{name}_count{labels_str} {count}")
                    lines.append(f"{name}_sum{labels_str} {total}")
                    lines.append(f"{name}_bucket{{le=\"+Inf\"{labels_str[1:]} {count}")
            
            # Export gauges
            for key, value in sorted(self._gauges.items()):
                name, labels_str = self._parse_key(key)
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name}{labels_str} {value}")
        
        return '\n'.join(lines) + '\n'
    
    def reset(self):
        """Reset all metrics (useful for testing)."""
        with self._lock:
            self._counters.clear()
            self._histograms.clear()
            self._gauges.clear()
    
    @staticmethod
    def _make_key(name: str, labels: Dict[str, str] = None) -> str:
        """Create metric key with labels."""
        if not labels:
            return name
        
        label_str = ','.join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    @staticmethod
    def _parse_key(key: str) -> tuple:
        """Parse metric key into name and labels string."""
        if '{' in key:
            name, rest = key.split('{', 1)
            return name, '{' + rest
        return key, ''


# Global metrics collector instance
_metrics = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics


def track_query_metrics(func: Callable) -> Callable:
    """
    Decorator to track query metrics automatically.
    
    Tracks:
    - Query count
    - Query duration
    - Success/error counts
    - Cache hits/misses
    
    Usage:
        @track_query_metrics
        async def query_endpoint(request: QueryRequest):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        metrics = get_metrics_collector()
        
        # Increment total queries
        metrics.increment_counter('mnn_queries_total')
        
        # Track duration
        start_time = time.time()
        
        try:
            # Execute function
            result = await func(*args, **kwargs)
            
            # Track success
            duration = time.time() - start_time
            metrics.observe_histogram('mnn_query_duration_seconds', duration, {'status': 'success'})
            metrics.increment_counter('mnn_queries_success_total')
            
            return result
            
        except Exception as e:
            # Track error
            duration = time.time() - start_time
            metrics.observe_histogram('mnn_query_duration_seconds', duration, {'status': 'error'})
            metrics.increment_counter('mnn_queries_error_total', labels={'error_type': type(e).__name__})
            
            raise
    
    return wrapper


def update_cache_metrics(cache_info):
    """
    Update cache-related metrics from cache_info tuple.
    
    Args:
        cache_info: namedtuple with hits, misses, maxsize, currsize
    """
    metrics = get_metrics_collector()
    
    metrics.set_gauge('mnn_cache_size', cache_info.currsize)
    metrics.set_gauge('mnn_cache_max_size', cache_info.maxsize)
    metrics.set_gauge('mnn_cache_hits_total', cache_info.hits)
    metrics.set_gauge('mnn_cache_misses_total', cache_info.misses)
    
    # Calculate hit rate
    total = cache_info.hits + cache_info.misses
    hit_rate = cache_info.hits / total if total > 0 else 0
    metrics.set_gauge('mnn_cache_hit_rate', hit_rate)


def track_slow_query(query: str, duration: float, threshold: float = 1.0):
    """
    Track queries that exceed duration threshold.
    
    Args:
        query: The query string
        duration: Query duration in seconds
        threshold: Threshold for "slow" queries (default: 1.0 second)
    """
    if duration > threshold:
        metrics = get_metrics_collector()
        metrics.increment_counter('mnn_slow_queries_total', labels={'threshold': str(threshold)})
        
        # Log slow query (imported here to avoid circular dependency)
        from logging_config import get_logger
        logger = get_logger(__name__)
        logger.warning(
            f"Slow query detected",
            extra={
                'query': query[:100],  # Truncate long queries
                'duration_seconds': duration,
                'threshold_seconds': threshold,
            }
        )
