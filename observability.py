"""
Observability module for MNN Pipeline.

Provides structured event logging, metrics tracking, and checkpointing
for the MNN knowledge engine pipeline stages.
"""
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import defaultdict
from threading import Lock

from config import config


def generate_event_id(normalized_query: str) -> str:
    """
    Generate deterministic event ID from normalized query using UUID5.
    
    Args:
        normalized_query: The normalized query string
        
    Returns:
        Deterministic UUID5 string
    """
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
    event_uuid = uuid.uuid5(namespace, normalized_query)
    return str(event_uuid)


class MetricsCollector:
    """
    Thread-safe metrics collector for pipeline operations.
    
    Tracks request counts, cache performance, and stage durations.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self._lock = Lock()
        self._request_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._stage_durations: Dict[str, List[float]] = defaultdict(list)
        self._last_durations: Dict[str, float] = {}
        self._error_count = 0
        self._max_duration_samples = 100  # Keep last N duration samples
    
    def increment_requests(self) -> None:
        """Increment total request count."""
        with self._lock:
            self._request_count += 1
    
    def increment_cache_hits(self) -> None:
        """Increment cache hit count."""
        with self._lock:
            self._cache_hits += 1
    
    def increment_cache_misses(self) -> None:
        """Increment cache miss count."""
        with self._lock:
            self._cache_misses += 1
    
    def increment_errors(self) -> None:
        """Increment error count."""
        with self._lock:
            self._error_count += 1
    
    def record_stage_duration(self, stage: str, duration: float) -> None:
        """
        Record duration for a pipeline stage.
        
        Args:
            stage: Stage name (normalize, constraints, indices, etc.)
            duration: Duration in seconds
        """
        with self._lock:
            # Keep only last N samples to avoid memory growth
            durations = self._stage_durations[stage]
            durations.append(duration)
            if len(durations) > self._max_duration_samples:
                durations.pop(0)
            
            self._last_durations[stage] = duration
    
    def get_snapshot(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot.
        
        Returns:
            Dictionary with current metrics (deterministic ordering)
        """
        with self._lock:
            snapshot = {
                "request_count": self._request_count,
                "error_count": self._error_count,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_hit_rate": (
                    self._cache_hits / (self._cache_hits + self._cache_misses)
                    if (self._cache_hits + self._cache_misses) > 0
                    else 0.0
                ),
                "last_stage_durations": dict(sorted(self._last_durations.items())),
            }
            
            # Add average durations for each stage
            avg_durations = {}
            for stage, durations in sorted(self._stage_durations.items()):
                if durations:
                    avg_durations[stage] = sum(durations) / len(durations)
            
            if avg_durations:
                snapshot["avg_stage_durations"] = avg_durations
            
            return snapshot


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector


class PipelineLogger:
    """
    Structured JSONL logger for pipeline stages.
    
    Logs each pipeline stage with event_id, stage name, duration,
    and stage-specific data.
    """
    
    def __init__(self, event_id: str, query: str, enabled: bool = None):
        """
        Initialize pipeline logger.
        
        Args:
            event_id: Unique event identifier
            query: The original query
            enabled: Whether logging is enabled (None = use config)
        """
        self.event_id = event_id
        self.query = query
        self.enabled = config.ENABLE_PIPELINE_LOGGING if enabled is None else enabled
        self.stage_start_times: Dict[str, float] = {}
    
    def log_stage(
        self,
        stage: str,
        action: str = "start",
        data: Optional[Dict[str, Any]] = None,
        duration: Optional[float] = None
    ) -> None:
        """
        Log a pipeline stage event.
        
        Args:
            stage: Stage name (normalize, constraints, indices, etc.)
            action: Action type (start, complete, error)
            data: Optional stage-specific data
            duration: Optional duration in seconds (for complete action)
        """
        if not self.enabled:
            return
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "event_type": "pipeline_stage",
            "event_id": self.event_id,
            "stage": stage,
            "action": action,
            "query": self.query[:100],  # Truncate for log size
        }
        
        if duration is not None:
            log_entry["duration_seconds"] = round(duration, 6)
        
        if data:
            log_entry["data"] = data
        
        # Write to stdout as JSONL
        print(json.dumps(log_entry, sort_keys=True))
    
    def start_stage(self, stage: str) -> None:
        """
        Mark the start of a pipeline stage.
        
        Args:
            stage: Stage name
        """
        self.stage_start_times[stage] = time.time()
        self.log_stage(stage, action="start")
    
    def complete_stage(self, stage: str, data: Optional[Dict[str, Any]] = None) -> float:
        """
        Mark the completion of a pipeline stage and return duration.
        
        Args:
            stage: Stage name
            data: Optional stage-specific data
            
        Returns:
            Duration in seconds
        """
        duration = time.time() - self.stage_start_times.get(stage, time.time())
        self.log_stage(stage, action="complete", data=data, duration=duration)
        
        # Record duration in metrics
        get_metrics_collector().record_stage_duration(stage, duration)
        
        return duration
    
    def error_stage(self, stage: str, error: str) -> None:
        """
        Log a pipeline stage error.
        
        Args:
            stage: Stage name
            error: Error message
        """
        duration = time.time() - self.stage_start_times.get(stage, time.time())
        self.log_stage(stage, action="error", data={"error": error}, duration=duration)


class CheckpointWriter:
    """
    Writer for deterministic pipeline checkpoints.
    
    Writes intermediate results (constraints, indices, results) to disk
    for debugging and auditing.
    """
    
    def __init__(self, event_id: str, enabled: bool = None):
        """
        Initialize checkpoint writer.
        
        Args:
            event_id: Unique event identifier
            enabled: Whether checkpoints are enabled (None = use config)
        """
        self.event_id = event_id
        self.enabled = config.ENABLE_CHECKPOINTS if enabled is None else enabled
        self.checkpoint_dir = Path(config.CHECKPOINT_DIR)
        
        if self.enabled:
            # Create checkpoint directory if it doesn't exist
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def write_checkpoint(self, step: str, data: Any) -> Optional[str]:
        """
        Write a checkpoint file.
        
        Args:
            step: Step name (constraints, indices, results, etc.)
            data: Data to write (will be JSON serialized)
            
        Returns:
            Path to checkpoint file if written, None if disabled
        """
        if not self.enabled:
            return None
        
        # Generate deterministic filename
        filename = f"{self.event_id}_{step}.json"
        filepath = self.checkpoint_dir / filename
        
        # Write checkpoint
        with open(filepath, 'w') as f:
            json.dump({
                "event_id": self.event_id,
                "step": step,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "data": data
            }, f, indent=2, sort_keys=True)
        
        return str(filepath)
