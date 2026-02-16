"""
Unit tests for MNN Observability module

Tests structured logging, metrics collection, and checkpoint writing.
"""

import unittest
import json
import os
import tempfile
import shutil
from pathlib import Path
from io import StringIO
from unittest.mock import patch

from observability import (
    generate_event_id,
    PipelineLogger,
    CheckpointWriter,
    MetricsCollector,
    get_metrics_collector,
)


class TestEventIDGeneration(unittest.TestCase):
    """Test cases for event ID generation."""
    
    def test_deterministic_event_id(self):
        """Test that event IDs are deterministic."""
        query1 = "ARTIFICIAL INTELLIGENCE"
        query2 = "ARTIFICIAL INTELLIGENCE"
        
        event_id1 = generate_event_id(query1)
        event_id2 = generate_event_id(query2)
        
        self.assertEqual(event_id1, event_id2)
    
    def test_different_queries_different_ids(self):
        """Test that different queries produce different event IDs."""
        query1 = "ARTIFICIAL INTELLIGENCE"
        query2 = "MACHINE LEARNING"
        
        event_id1 = generate_event_id(query1)
        event_id2 = generate_event_id(query2)
        
        self.assertNotEqual(event_id1, event_id2)
    
    def test_event_id_format(self):
        """Test that event ID is a valid UUID string."""
        query = "TEST QUERY"
        event_id = generate_event_id(query)
        
        # Should be a UUID string format
        self.assertIsInstance(event_id, str)
        self.assertEqual(len(event_id), 36)  # UUID format: 8-4-4-4-12
        self.assertEqual(event_id.count('-'), 4)


class TestMetricsCollector(unittest.TestCase):
    """Test cases for metrics collection."""
    
    def setUp(self):
        """Set up a fresh metrics collector."""
        self.metrics = MetricsCollector()
    
    def test_initial_state(self):
        """Test that metrics start at zero."""
        snapshot = self.metrics.get_snapshot()
        
        self.assertEqual(snapshot['request_count'], 0)
        self.assertEqual(snapshot['error_count'], 0)
        self.assertEqual(snapshot['cache_hits'], 0)
        self.assertEqual(snapshot['cache_misses'], 0)
        self.assertEqual(snapshot['cache_hit_rate'], 0.0)
    
    def test_increment_requests(self):
        """Test request counting."""
        self.metrics.increment_requests()
        self.metrics.increment_requests()
        
        snapshot = self.metrics.get_snapshot()
        self.assertEqual(snapshot['request_count'], 2)
    
    def test_increment_errors(self):
        """Test error counting."""
        self.metrics.increment_errors()
        
        snapshot = self.metrics.get_snapshot()
        self.assertEqual(snapshot['error_count'], 1)
    
    def test_cache_hit_rate(self):
        """Test cache hit rate calculation."""
        self.metrics.increment_cache_hits()
        self.metrics.increment_cache_hits()
        self.metrics.increment_cache_hits()
        self.metrics.increment_cache_misses()
        
        snapshot = self.metrics.get_snapshot()
        self.assertEqual(snapshot['cache_hits'], 3)
        self.assertEqual(snapshot['cache_misses'], 1)
        self.assertEqual(snapshot['cache_hit_rate'], 0.75)
    
    def test_stage_duration_recording(self):
        """Test stage duration recording."""
        self.metrics.record_stage_duration("normalize", 0.001)
        self.metrics.record_stage_duration("constraints", 0.002)
        self.metrics.record_stage_duration("normalize", 0.003)
        
        snapshot = self.metrics.get_snapshot()
        
        # Check last durations
        self.assertEqual(snapshot['last_stage_durations']['normalize'], 0.003)
        self.assertEqual(snapshot['last_stage_durations']['constraints'], 0.002)
        
        # Check average durations
        self.assertAlmostEqual(snapshot['avg_stage_durations']['normalize'], 0.002)
        self.assertEqual(snapshot['avg_stage_durations']['constraints'], 0.002)
    
    def test_snapshot_deterministic(self):
        """Test that snapshot keys are sorted (deterministic)."""
        self.metrics.increment_requests()
        self.metrics.record_stage_duration("zzz", 0.1)
        self.metrics.record_stage_duration("aaa", 0.2)
        
        snapshot = self.metrics.get_snapshot()
        
        # Check that stage durations are sorted
        duration_keys = list(snapshot['last_stage_durations'].keys())
        self.assertEqual(duration_keys, sorted(duration_keys))


class TestPipelineLogger(unittest.TestCase):
    """Test cases for pipeline logging."""
    
    def test_logger_enabled_by_default(self):
        """Test that logger uses config default."""
        logger = PipelineLogger("test-event-id", "test query")
        # Just verify it doesn't crash
        logger.start_stage("test")
        logger.complete_stage("test")
    
    def test_logger_can_be_disabled(self):
        """Test that logging can be disabled."""
        logger = PipelineLogger("test-event-id", "test query", enabled=False)
        
        # Should not produce output when disabled
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            logger.start_stage("test")
            logger.complete_stage("test")
            output = mock_stdout.getvalue()
            self.assertEqual(output, "")
    
    def test_logger_produces_jsonl(self):
        """Test that logger produces valid JSONL output."""
        logger = PipelineLogger("test-event-id", "test query", enabled=True)
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            logger.start_stage("normalize")
            output = mock_stdout.getvalue()
            
            # Should be valid JSON
            lines = output.strip().split('\n')
            self.assertEqual(len(lines), 1)
            
            log_entry = json.loads(lines[0])
            self.assertEqual(log_entry['event_type'], 'pipeline_stage')
            self.assertEqual(log_entry['event_id'], 'test-event-id')
            self.assertEqual(log_entry['stage'], 'normalize')
            self.assertEqual(log_entry['action'], 'start')
            self.assertIn('timestamp', log_entry)
    
    def test_logger_complete_stage_includes_duration(self):
        """Test that complete stage includes duration."""
        logger = PipelineLogger("test-event-id", "test query", enabled=True)
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            logger.start_stage("test")
            duration = logger.complete_stage("test")
            output = mock_stdout.getvalue()
            
            # Should have two lines: start and complete
            lines = output.strip().split('\n')
            self.assertEqual(len(lines), 2)
            
            complete_entry = json.loads(lines[1])
            self.assertEqual(complete_entry['action'], 'complete')
            self.assertIn('duration_seconds', complete_entry)
            self.assertGreaterEqual(complete_entry['duration_seconds'], 0)
            self.assertIsInstance(duration, float)
            self.assertGreaterEqual(duration, 0)
    
    def test_logger_error_stage(self):
        """Test error stage logging."""
        logger = PipelineLogger("test-event-id", "test query", enabled=True)
        
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            logger.start_stage("test")
            logger.error_stage("test", "Something went wrong")
            output = mock_stdout.getvalue()
            
            lines = output.strip().split('\n')
            error_entry = json.loads(lines[1])
            
            self.assertEqual(error_entry['action'], 'error')
            self.assertEqual(error_entry['data']['error'], 'Something went wrong')


class TestCheckpointWriter(unittest.TestCase):
    """Test cases for checkpoint writing."""
    
    def setUp(self):
        """Set up temporary directory for checkpoints."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_checkpoint_disabled_by_default(self):
        """Test that checkpoint writing can be disabled."""
        writer = CheckpointWriter("test-event-id", enabled=False)
        result = writer.write_checkpoint("test", {"data": "value"})
        
        self.assertIsNone(result)
    
    def test_checkpoint_creates_directory(self):
        """Test that checkpoint directory is created."""
        checkpoint_dir = os.path.join(self.temp_dir, "test_checkpoints")
        
        # Override config for testing
        with patch('observability.config.CHECKPOINT_DIR', checkpoint_dir):
            writer = CheckpointWriter("test-event-id", enabled=True)
            
            self.assertTrue(os.path.exists(checkpoint_dir))
    
    def test_checkpoint_writes_file(self):
        """Test that checkpoint writes a file."""
        checkpoint_dir = os.path.join(self.temp_dir, "test_checkpoints")
        
        with patch('observability.config.CHECKPOINT_DIR', checkpoint_dir):
            writer = CheckpointWriter("test-event-123", enabled=True)
            filepath = writer.write_checkpoint("constraints", {"pattern": "TEST"})
            
            self.assertIsNotNone(filepath)
            self.assertTrue(os.path.exists(filepath))
            
            # Verify filename format
            self.assertIn("test-event-123_constraints.json", filepath)
    
    def test_checkpoint_file_content(self):
        """Test checkpoint file content structure."""
        checkpoint_dir = os.path.join(self.temp_dir, "test_checkpoints")
        
        with patch('observability.config.CHECKPOINT_DIR', checkpoint_dir):
            writer = CheckpointWriter("test-event-456", enabled=True)
            test_data = {"pattern": "TEST", "length": 4}
            filepath = writer.write_checkpoint("constraints", test_data)
            
            # Read and verify content
            with open(filepath, 'r') as f:
                content = json.load(f)
            
            self.assertEqual(content['event_id'], 'test-event-456')
            self.assertEqual(content['step'], 'constraints')
            self.assertIn('timestamp', content)
            self.assertEqual(content['data'], test_data)
    
    def test_checkpoint_deterministic_filename(self):
        """Test that checkpoint filenames are deterministic."""
        checkpoint_dir = os.path.join(self.temp_dir, "test_checkpoints")
        
        with patch('observability.config.CHECKPOINT_DIR', checkpoint_dir):
            writer1 = CheckpointWriter("event-abc", enabled=True)
            writer2 = CheckpointWriter("event-abc", enabled=True)
            
            filepath1 = writer1.write_checkpoint("test", {})
            # Delete file
            os.remove(filepath1)
            filepath2 = writer2.write_checkpoint("test", {})
            
            # Filenames should be identical (deterministic)
            self.assertEqual(os.path.basename(filepath1), os.path.basename(filepath2))


if __name__ == '__main__':
    unittest.main()
