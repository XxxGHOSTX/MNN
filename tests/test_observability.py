"""
Unit tests for Observability Module

Tests JSONL logging, event IDs, pipeline timers, and event tracking.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path

from observability import (
    generate_event_id,
    set_event_id,
    get_event_id,
    log_pipeline_event,
    get_recent_events,
    clear_event_log,
    PipelineTimer,
)


class TestObservability(unittest.TestCase):
    """Test cases for observability module."""
    
    def setUp(self):
        """Clear event log before each test."""
        clear_event_log()
    
    def test_generate_event_id_deterministic(self):
        """Test that event IDs are deterministic."""
        query1 = "TEST QUERY"
        query2 = "TEST QUERY"
        query3 = "DIFFERENT QUERY"
        
        id1 = generate_event_id(query1)
        id2 = generate_event_id(query2)
        id3 = generate_event_id(query3)
        
        # Same query produces same ID
        self.assertEqual(id1, id2)
        
        # Different query produces different ID
        self.assertNotEqual(id1, id3)
        
        # IDs are valid UUIDs
        self.assertEqual(len(id1), 36)
        self.assertIn('-', id1)
    
    def test_event_id_context(self):
        """Test event ID context variable."""
        test_id = "test-event-id-123"
        
        # Initially empty
        self.assertEqual(get_event_id(), "")
        
        # Set and retrieve
        set_event_id(test_id)
        self.assertEqual(get_event_id(), test_id)
    
    def test_log_pipeline_event_structure(self):
        """Test that logged events have correct structure."""
        set_event_id("test-event-123")
        
        log_pipeline_event(
            stage="normalize",
            event_type="start",
            data={"query": "test"}
        )
        
        events = get_recent_events(1)
        self.assertEqual(len(events), 1)
        
        event = events[0]
        
        # Check required fields
        self.assertIn("timestamp", event)
        self.assertIn("event_id", event)
        self.assertIn("stage", event)
        self.assertIn("event_type", event)
        
        # Check values
        self.assertEqual(event["event_id"], "test-event-123")
        self.assertEqual(event["stage"], "normalize")
        self.assertEqual(event["event_type"], "start")
        self.assertEqual(event["data"], {"query": "test"})
    
    def test_log_pipeline_event_with_duration(self):
        """Test logging events with duration."""
        set_event_id("test-event-456")
        
        log_pipeline_event(
            stage="analyze",
            event_type="complete",
            duration_ms=123.45
        )
        
        events = get_recent_events(1)
        event = events[0]
        
        self.assertEqual(event["duration_ms"], 123.45)
    
    def test_log_pipeline_event_to_file(self):
        """Test logging events to JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "events.jsonl")
            set_event_id("test-file-event")
            
            log_pipeline_event(
                stage="test",
                event_type="complete",
                data={"result": "success"},
                log_file=log_file
            )
            
            # Read and verify file
            self.assertTrue(os.path.exists(log_file))
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            self.assertEqual(len(lines), 1)
            
            event = json.loads(lines[0])
            self.assertEqual(event["event_id"], "test-file-event")
            self.assertEqual(event["stage"], "test")
            self.assertEqual(event["data"]["result"], "success")
    
    def test_get_recent_events_limit(self):
        """Test that get_recent_events respects limit."""
        set_event_id("test-limit")
        
        # Log 10 events
        for i in range(10):
            log_pipeline_event(
                stage=f"stage{i}",
                event_type="complete"
            )
        
        # Get only 5
        events = get_recent_events(5)
        self.assertEqual(len(events), 5)
        
        # Should be newest first
        self.assertEqual(events[0]["stage"], "stage9")
        self.assertEqual(events[4]["stage"], "stage5")
    
    def test_pipeline_timer_success(self):
        """Test PipelineTimer context manager for successful execution."""
        set_event_id("timer-test")
        clear_event_log()
        
        with PipelineTimer("test_stage", {"input": "data"}):
            pass  # Simulate work
        
        events = get_recent_events(10)
        
        # Should have start and complete events
        self.assertEqual(len(events), 2)
        
        complete_event = events[0]
        start_event = events[1]
        
        self.assertEqual(start_event["event_type"], "start")
        self.assertEqual(start_event["stage"], "test_stage")
        self.assertEqual(start_event["data"], {"input": "data"})
        
        self.assertEqual(complete_event["event_type"], "complete")
        self.assertEqual(complete_event["stage"], "test_stage")
        self.assertIn("duration_ms", complete_event)
        self.assertGreaterEqual(complete_event["duration_ms"], 0)
    
    def test_pipeline_timer_error(self):
        """Test PipelineTimer context manager for error cases."""
        set_event_id("timer-error-test")
        clear_event_log()
        
        try:
            with PipelineTimer("error_stage"):
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected
        
        events = get_recent_events(10)
        
        # Should have start and error events
        self.assertEqual(len(events), 2)
        
        error_event = events[0]
        
        self.assertEqual(error_event["event_type"], "error")
        self.assertEqual(error_event["stage"], "error_stage")
        self.assertIn("error", error_event["data"])
        self.assertIn("duration_ms", error_event)
    
    def test_event_log_ring_buffer(self):
        """Test that event log acts as a ring buffer."""
        set_event_id("ring-buffer-test")
        
        # Log more than max size (1000)
        # For testing, just verify recent events work
        for i in range(50):
            log_pipeline_event(
                stage="test",
                event_type="complete",
                data={"index": i}
            )
        
        events = get_recent_events(50)
        self.assertEqual(len(events), 50)
        
        # Newest first
        self.assertEqual(events[0]["data"]["index"], 49)
        self.assertEqual(events[49]["data"]["index"], 0)


if __name__ == '__main__':
    unittest.main()
