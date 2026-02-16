"""
Observability Module for MNN Pipeline

Provides structured JSONL logging per pipeline stage with deterministic event IDs
and performance metrics tracking. Supports full observability of the MNN pipeline
without compromising determinism.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextvars import ContextVar

# Context variable for current event ID (deterministic per request)
event_id_var: ContextVar[str] = ContextVar('event_id', default='')

# In-memory event log for /metricsz endpoint (limited size)
_event_log: List[Dict[str, Any]] = []
_MAX_EVENT_LOG_SIZE = 1000


def generate_event_id(normalized_query: str) -> str:
    """
    Generate deterministic event ID using UUID5.
    
    Uses UUID5 with a fixed namespace to ensure the same normalized query
    always produces the same event ID, preserving determinism.
    
    Args:
        normalized_query: The normalized query string
        
    Returns:
        Deterministic event ID string
    """
    # Use DNS namespace for consistency
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
    event_uuid = uuid.uuid5(namespace, normalized_query)
    return str(event_uuid)


def set_event_id(event_id: str) -> None:
    """Set the current event ID in context."""
    event_id_var.set(event_id)


def get_event_id() -> str:
    """Get the current event ID from context."""
    return event_id_var.get()


def log_pipeline_event(
    stage: str,
    event_type: str,
    data: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[float] = None,
    log_file: Optional[str] = None
) -> None:
    """
    Log a pipeline event in structured JSONL format.
    
    Each event is logged with:
    - timestamp (ISO 8601)
    - event_id (deterministic uuid5)
    - stage (pipeline stage name)
    - event_type (e.g., "start", "complete", "error")
    - data (stage-specific data)
    - duration_ms (optional, for completion events)
    
    Args:
        stage: Pipeline stage name (e.g., "normalize", "constraints")
        event_type: Event type (e.g., "start", "complete", "error")
        data: Optional dictionary with stage-specific data
        duration_ms: Optional duration in milliseconds
        log_file: Optional log file path (defaults to None for in-memory only)
    """
    event_id = get_event_id()
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_id": event_id,
        "stage": stage,
        "event_type": event_type,
    }
    
    if data:
        log_entry["data"] = data
    
    if duration_ms is not None:
        log_entry["duration_ms"] = duration_ms
    
    # Add to in-memory log (ring buffer)
    global _event_log
    _event_log.append(log_entry)
    if len(_event_log) > _MAX_EVENT_LOG_SIZE:
        _event_log.pop(0)
    
    # Optionally write to file
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')


def get_recent_events(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get recent events from in-memory log.
    
    Args:
        limit: Maximum number of events to return
        
    Returns:
        List of recent events (newest first)
    """
    return list(reversed(_event_log[-limit:]))


def clear_event_log() -> None:
    """Clear the in-memory event log. Used for testing."""
    global _event_log
    _event_log.clear()


class PipelineTimer:
    """
    Context manager for timing pipeline stages.
    
    Automatically logs start and complete events with duration.
    
    Example:
        with PipelineTimer("normalize", {"query": "test"}):
            result = normalize_query("test")
    """
    
    def __init__(
        self,
        stage: str,
        start_data: Optional[Dict[str, Any]] = None,
        log_file: Optional[str] = None
    ):
        """
        Initialize timer.
        
        Args:
            stage: Pipeline stage name
            start_data: Optional data to log at start
            log_file: Optional log file path
        """
        self.stage = stage
        self.start_data = start_data
        self.log_file = log_file
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        """Start timing and log start event."""
        import time
        self.start_time = time.perf_counter()
        log_pipeline_event(
            stage=self.stage,
            event_type="start",
            data=self.start_data,
            log_file=self.log_file
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log complete/error event."""
        import time
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        
        if exc_type is not None:
            # Error occurred
            log_pipeline_event(
                stage=self.stage,
                event_type="error",
                data={"error": str(exc_val)},
                duration_ms=duration_ms,
                log_file=self.log_file
            )
        else:
            # Successful completion
            log_pipeline_event(
                stage=self.stage,
                event_type="complete",
                duration_ms=duration_ms,
                log_file=self.log_file
            )
        
        return False  # Don't suppress exceptions
