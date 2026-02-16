"""
Unit tests for Checkpoints Module

Tests checkpoint save/load, replay, and management functionality.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path

from checkpoints import CheckpointManager, replay_checkpoint


class TestCheckpoints(unittest.TestCase):
    """Test cases for checkpoints module."""
    
    def setUp(self):
        """Create temporary checkpoint directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = CheckpointManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_checkpoint(self):
        """Test saving a checkpoint."""
        event_id = "test-event-123"
        
        checkpoint_file = self.manager.save_checkpoint(
            event_id=event_id,
            query="test query",
            normalized_query="TEST QUERY",
            constraints={"key": "value"},
            indices=[0, 1, 2],
            sequences=["seq1", "seq2"],
            results=[{"sequence": "result1", "score": 1.0}],
            timings={"total_ms": 100.5}
        )
        
        # Check file was created
        self.assertTrue(Path(checkpoint_file).exists())
        self.assertTrue(checkpoint_file.endswith(f"{event_id}.json"))
        
        # Check file content
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["event_id"], event_id)
        self.assertEqual(data["query"], "test query")
        self.assertEqual(data["normalized_query"], "TEST QUERY")
        self.assertEqual(data["constraints"], {"key": "value"})
        self.assertEqual(data["indices"], [0, 1, 2])
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["timings"]["total_ms"], 100.5)
    
    def test_load_checkpoint(self):
        """Test loading a checkpoint."""
        event_id = "test-load-456"
        
        # Save first
        self.manager.save_checkpoint(
            event_id=event_id,
            query="load test",
            normalized_query="LOAD TEST",
            constraints={"test": True},
            indices=[10, 20],
            sequences=["a", "b"],
            results=[{"sequence": "result", "score": 0.9}],
        )
        
        # Load
        checkpoint = self.manager.load_checkpoint(event_id)
        
        self.assertEqual(checkpoint["event_id"], event_id)
        self.assertEqual(checkpoint["query"], "load test")
        self.assertEqual(checkpoint["normalized_query"], "LOAD TEST")
        self.assertEqual(checkpoint["constraints"], {"test": True})
        self.assertEqual(checkpoint["indices"], [10, 20])
    
    def test_load_checkpoint_not_found(self):
        """Test loading non-existent checkpoint raises error."""
        with self.assertRaises(FileNotFoundError):
            self.manager.load_checkpoint("does-not-exist")
    
    def test_list_checkpoints(self):
        """Test listing checkpoints."""
        # Initially empty
        checkpoints = self.manager.list_checkpoints()
        self.assertEqual(len(checkpoints), 0)
        
        # Save some checkpoints
        self.manager.save_checkpoint(
            event_id="checkpoint-1",
            query="q1",
            normalized_query="Q1",
            constraints={},
            indices=[],
            sequences=[],
            results=[],
        )
        self.manager.save_checkpoint(
            event_id="checkpoint-2",
            query="q2",
            normalized_query="Q2",
            constraints={},
            indices=[],
            sequences=[],
            results=[],
        )
        
        # List
        checkpoints = self.manager.list_checkpoints()
        self.assertEqual(len(checkpoints), 2)
        self.assertIn("checkpoint-1", checkpoints)
        self.assertIn("checkpoint-2", checkpoints)
        
        # Should be sorted
        self.assertEqual(checkpoints, sorted(checkpoints))
    
    def test_delete_checkpoint(self):
        """Test deleting a checkpoint."""
        event_id = "delete-test"
        
        # Save
        self.manager.save_checkpoint(
            event_id=event_id,
            query="test",
            normalized_query="TEST",
            constraints={},
            indices=[],
            sequences=[],
            results=[],
        )
        
        # Verify exists
        checkpoints = self.manager.list_checkpoints()
        self.assertIn(event_id, checkpoints)
        
        # Delete
        result = self.manager.delete_checkpoint(event_id)
        self.assertTrue(result)
        
        # Verify deleted
        checkpoints = self.manager.list_checkpoints()
        self.assertNotIn(event_id, checkpoints)
    
    def test_delete_checkpoint_not_found(self):
        """Test deleting non-existent checkpoint."""
        result = self.manager.delete_checkpoint("does-not-exist")
        self.assertFalse(result)
    
    def test_replay_checkpoint(self):
        """Test replaying a checkpoint."""
        event_id = "replay-test"
        
        # Save
        self.manager.save_checkpoint(
            event_id=event_id,
            query="replay query",
            normalized_query="REPLAY QUERY",
            constraints={"key": "val"},
            indices=[1, 2, 3],
            sequences=["seq"],
            results=[
                {"sequence": "result1", "score": 1.0},
                {"sequence": "result2", "score": 0.8},
            ],
            timings={"total_ms": 250.0, "normalize_ms": 50.0}
        )
        
        # Replay
        result = replay_checkpoint(self.manager, event_id)
        
        self.assertEqual(result["event_id"], event_id)
        self.assertEqual(result["query"], "replay query")
        self.assertEqual(result["normalized_query"], "REPLAY QUERY")
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["score"], 1.0)
        self.assertEqual(result["timings"]["total_ms"], 250.0)
        self.assertEqual(result["checkpoint_file"], f"{event_id}.json")
    
    def test_checkpoint_determinism(self):
        """Test that checkpoints are deterministic."""
        event_id_1 = "determinism-1"
        event_id_2 = "determinism-2"
        
        # Save identical data with different event IDs
        data_1 = {
            "event_id": event_id_1,
            "query": "same query",
            "normalized_query": "SAME QUERY",
            "constraints": {"a": 1, "b": 2},
            "indices": [1, 2, 3],
            "sequences": ["x", "y"],
            "results": [{"sequence": "r", "score": 1.0}],
            "timings": {"total_ms": 100}
        }
        
        data_2 = {
            "event_id": event_id_2,
            "query": "same query",
            "normalized_query": "SAME QUERY",
            "constraints": {"a": 1, "b": 2},
            "indices": [1, 2, 3],
            "sequences": ["x", "y"],
            "results": [{"sequence": "r", "score": 1.0}],
            "timings": {"total_ms": 100}
        }
        
        self.manager.save_checkpoint(**data_1)
        self.manager.save_checkpoint(**data_2)
        
        cp1 = self.manager.load_checkpoint(event_id_1)
        cp2 = self.manager.load_checkpoint(event_id_2)
        
        # Everything except event_id should match
        self.assertEqual(cp1["query"], cp2["query"])
        self.assertEqual(cp1["normalized_query"], cp2["normalized_query"])
        self.assertEqual(cp1["constraints"], cp2["constraints"])
        self.assertEqual(cp1["indices"], cp2["indices"])
        self.assertEqual(cp1["results"], cp2["results"])
        self.assertEqual(cp1["timings"], cp2["timings"])


if __name__ == '__main__':
    unittest.main()
