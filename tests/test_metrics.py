"""
Unit tests for Metrics Module

Tests metrics tracking, counters, timings, and snapshot generation.
"""

import unittest
import time

from metrics import (
    increment_counter,
    record_timing,
    record_request,
    update_cache_stats,
    get_metrics_snapshot,
    reset_metrics,
)


class TestMetrics(unittest.TestCase):
    """Test cases for metrics module."""
    
    def setUp(self):
        """Reset metrics before each test."""
        reset_metrics()
    
    def test_increment_counter(self):
        """Test counter incrementation."""
        increment_counter("test.counter")
        increment_counter("test.counter")
        increment_counter("test.counter", 3)
        
        snapshot = get_metrics_snapshot()
        self.assertEqual(snapshot["counters"]["test.counter"], 5)
    
    def test_multiple_counters(self):
        """Test multiple independent counters."""
        increment_counter("counter.a")
        increment_counter("counter.b", 2)
        increment_counter("counter.a")
        
        snapshot = get_metrics_snapshot()
        self.assertEqual(snapshot["counters"]["counter.a"], 2)
        self.assertEqual(snapshot["counters"]["counter.b"], 2)
    
    def test_record_timing(self):
        """Test timing recording."""
        record_timing("test.timing", 100.5)
        record_timing("test.timing", 200.5)
        record_timing("test.timing", 150.5)
        
        snapshot = get_metrics_snapshot()
        timing = snapshot["timings"]["test.timing"]
        
        self.assertEqual(timing["count"], 3)
        self.assertEqual(timing["min"], 100.5)
        self.assertEqual(timing["max"], 200.5)
        self.assertAlmostEqual(timing["avg"], 150.5, places=1)
        self.assertEqual(timing["p50"], 150.5)
    
    def test_timing_percentiles(self):
        """Test timing percentile calculations."""
        # Record 100 values
        for i in range(100):
            record_timing("percentile.test", float(i))
        
        snapshot = get_metrics_snapshot()
        timing = snapshot["timings"]["percentile.test"]
        
        self.assertEqual(timing["count"], 100)
        self.assertEqual(timing["min"], 0.0)
        self.assertEqual(timing["max"], 99.0)
        self.assertAlmostEqual(timing["avg"], 49.5, places=1)
        self.assertAlmostEqual(timing["p50"], 49.0, delta=1)
        self.assertAlmostEqual(timing["p95"], 94.0, delta=1)
        self.assertAlmostEqual(timing["p99"], 98.0, delta=1)
    
    def test_record_request(self):
        """Test request metadata recording."""
        record_request({
            "event_id": "test-123",
            "query_length": 50,
            "result_count": 5,
            "total_ms": 123.45,
        })
        
        snapshot = get_metrics_snapshot()
        requests = snapshot["recent_requests"]
        
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["event_id"], "test-123")
        self.assertEqual(requests[0]["query_length"], 50)
    
    def test_recent_requests_limit(self):
        """Test that recent requests are limited."""
        # Record many requests
        for i in range(50):
            record_request({
                "event_id": f"event-{i}",
                "query_length": i,
            })
        
        snapshot = get_metrics_snapshot()
        requests = snapshot["recent_requests"]
        
        # Should only return last 20
        self.assertEqual(len(requests), 20)
        
        # Should be from index 30-49 (last 20)
        # They're returned in reverse order (newest first in the slice)
        self.assertIn("event-", requests[0]["event_id"])
        self.assertIn("event-", requests[19]["event_id"])
    
    def test_update_cache_stats(self):
        """Test cache statistics update."""
        update_cache_stats("test_cache", {
            "hits": 100,
            "misses": 20,
            "currsize": 50,
            "maxsize": 128,
        })
        
        snapshot = get_metrics_snapshot()
        cache = snapshot["cache_stats"]["test_cache"]
        
        self.assertEqual(cache["hits"], 100)
        self.assertEqual(cache["misses"], 20)
        self.assertEqual(cache["size"], 50)
        self.assertEqual(cache["maxsize"], 128)
    
    def test_snapshot_structure(self):
        """Test metrics snapshot has correct structure."""
        increment_counter("test.count")
        record_timing("test.time", 100)
        update_cache_stats("cache", {"hits": 10, "misses": 2, "currsize": 5, "maxsize": 10})
        record_request({"event_id": "test"})
        
        snapshot = get_metrics_snapshot()
        
        # Check required keys
        self.assertIn("timestamp", snapshot)
        self.assertIn("counters", snapshot)
        self.assertIn("timings", snapshot)
        self.assertIn("cache_stats", snapshot)
        self.assertIn("recent_requests", snapshot)
        
        # Check types
        self.assertIsInstance(snapshot["timestamp"], float)
        self.assertIsInstance(snapshot["counters"], dict)
        self.assertIsInstance(snapshot["timings"], dict)
        self.assertIsInstance(snapshot["cache_stats"], dict)
        self.assertIsInstance(snapshot["recent_requests"], list)
    
    def test_reset_metrics(self):
        """Test metrics reset."""
        increment_counter("test")
        record_timing("test", 100)
        update_cache_stats("test", {"hits": 10, "misses": 2, "currsize": 5, "maxsize": 10})
        record_request({"event_id": "test"})
        
        reset_metrics()
        
        snapshot = get_metrics_snapshot()
        self.assertEqual(len(snapshot["counters"]), 0)
        self.assertEqual(len(snapshot["timings"]), 0)
        self.assertEqual(len(snapshot["cache_stats"]), 0)
        self.assertEqual(len(snapshot["recent_requests"]), 0)
    
    def test_timing_ring_buffer(self):
        """Test that timing samples are limited."""
        # Record more than max (1000)
        for i in range(1500):
            record_timing("buffer.test", float(i))
        
        snapshot = get_metrics_snapshot()
        timing = snapshot["timings"]["buffer.test"]
        
        # Should only keep last 1000
        self.assertEqual(timing["count"], 1000)
        # Min should be 500 (first 500 dropped)
        self.assertEqual(timing["min"], 500.0)


if __name__ == '__main__':
    unittest.main()
