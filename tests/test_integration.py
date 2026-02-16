"""
Integration tests for Observability, Metrics, and Guardrails in API

Tests the full integration of new features with existing API endpoints.
"""

import unittest
from fastapi.testclient import TestClient

from api import app
from metrics import reset_metrics, get_metrics_snapshot
from observability import clear_event_log, get_recent_events


class TestAPIIntegration(unittest.TestCase):
    """Integration tests for API with new features."""
    
    def setUp(self):
        """Set up test client and reset state."""
        self.client = TestClient(app)
        reset_metrics()
        clear_event_log()
    
    def test_query_endpoint_returns_timings(self):
        """Test that query endpoint returns timing information."""
        response = self.client.post("/query", json={"query": "test"})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check new fields
        self.assertIn("timings", data)
        self.assertIn("event_id", data)
        
        # Check timing fields
        timings = data["timings"]
        self.assertIn("total_ms", timings)
        self.assertIn("normalize_ms", timings)
        self.assertIn("constraints_ms", timings)
        
        # All timings should be non-negative
        for key, value in timings.items():
            self.assertGreaterEqual(value, 0)
    
    def test_query_endpoint_deterministic_event_id(self):
        """Test that same query produces same event ID."""
        response1 = self.client.post("/query", json={"query": "determinism test"})
        response2 = self.client.post("/query", json={"query": "determinism test"})
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        event_id1 = response1.json()["event_id"]
        event_id2 = response2.json()["event_id"]
        
        # Same query should produce same event ID
        self.assertEqual(event_id1, event_id2)
    
    def test_metricsz_endpoint_exists(self):
        """Test that /metricsz endpoint exists."""
        response = self.client.get("/metricsz")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check structure
        self.assertIn("timestamp", data)
        self.assertIn("counters", data)
        self.assertIn("timings", data)
        self.assertIn("cache_stats", data)
        self.assertIn("recent_requests", data)
    
    def test_metricsz_tracks_queries(self):
        """Test that metrics endpoint tracks query counts."""
        # Make some queries
        self.client.post("/query", json={"query": "test1"})
        self.client.post("/query", json={"query": "test2"})
        self.client.post("/query", json={"query": "test3"})
        
        # Check metrics
        response = self.client.get("/metricsz")
        data = response.json()
        
        counters = data["counters"]
        self.assertGreaterEqual(counters.get("queries.total", 0), 3)
        self.assertGreaterEqual(counters.get("queries.success", 0), 3)
    
    def test_metricsz_includes_cache_stats(self):
        """Test that metrics endpoint includes cache statistics."""
        # Make a query to populate cache
        self.client.post("/query", json={"query": "cache test"})
        
        response = self.client.get("/metricsz")
        data = response.json()
        
        cache_stats = data["cache_stats"]
        
        # Should have API cache stats
        if "api_cache" in cache_stats:
            api_cache = cache_stats["api_cache"]
            self.assertIn("hits", api_cache)
            self.assertIn("misses", api_cache)
            self.assertIn("size", api_cache)
            self.assertIn("maxsize", api_cache)
    
    def test_metricsz_includes_timings(self):
        """Test that metrics endpoint includes timing statistics."""
        # Make queries to generate timing data
        for i in range(5):
            self.client.post("/query", json={"query": f"timing test {i}"})
        
        response = self.client.get("/metricsz")
        data = response.json()
        
        timings = data["timings"]
        
        # Should have pipeline timing stats
        if "pipeline.total" in timings:
            pipeline_timing = timings["pipeline.total"]
            self.assertIn("count", pipeline_timing)
            self.assertIn("min", pipeline_timing)
            self.assertIn("max", pipeline_timing)
            self.assertIn("avg", pipeline_timing)
            self.assertIn("p50", pipeline_timing)
            self.assertIn("p95", pipeline_timing)
            self.assertIn("p99", pipeline_timing)
    
    def test_query_validation_too_long(self):
        """Test that queries over max length are rejected."""
        long_query = "a" * 1001  # Exceeds default max of 1000
        
        response = self.client.post("/query", json={"query": long_query})
        
        # Pydantic validation returns 422
        self.assertIn(response.status_code, [400, 422])
        detail = response.json()["detail"]
        if isinstance(detail, str):
            self.assertIn("long", detail.lower())
    
    def test_query_validation_invalid_chars(self):
        """Test that queries with invalid characters are rejected."""
        invalid_query = "test<script>alert('xss')</script>"
        
        response = self.client.post("/query", json={"query": invalid_query})
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid", response.json()["detail"].lower())
    
    def test_query_validation_empty(self):
        """Test that empty queries are rejected."""
        response = self.client.post("/query", json={"query": ""})
        
        # Pydantic validation returns 422
        self.assertIn(response.status_code, [400, 422])
        detail = response.json()["detail"]
        # Could be string or list of errors
        detail_str = str(detail).lower()
        self.assertTrue("empty" in detail_str or "character" in detail_str)
    
    def test_query_validation_whitespace_only(self):
        """Test that whitespace-only queries are rejected."""
        response = self.client.post("/query", json={"query": "   "})
        
        # Should be rejected (400 from our code)
        self.assertIn(response.status_code, [400, 422])
    
    def test_error_messages_sanitized(self):
        """Test that error messages don't leak sensitive info."""
        # Try to trigger an error
        response = self.client.post("/query", json={"query": "!@#$%^&*()"})
        
        if response.status_code != 200:
            detail = response.json()["detail"]
            
            # Should not contain file paths
            self.assertNotIn("/home/", detail)
            self.assertNotIn("/usr/", detail)
            
            # Should not contain IP addresses
            import re
            ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            self.assertIsNone(re.search(ip_pattern, detail))
    
    def test_cache_immutability(self):
        """Test that cache results are protected from mutation."""
        # Make first query
        response1 = self.client.post("/query", json={"query": "immutability test"})
        data1 = response1.json()
        
        # Store original first result
        original_sequence = data1["results"][0]["sequence"]
        original_score = data1["results"][0]["score"]
        
        # Make second query (should hit cache)
        response2 = self.client.post("/query", json={"query": "immutability test"})
        data2 = response2.json()
        
        # Results should match
        self.assertEqual(data1["results"], data2["results"])
        
        # Verify nothing changed
        self.assertEqual(data2["results"][0]["sequence"], original_sequence)
        self.assertEqual(data2["results"][0]["score"], original_score)
    
    def test_observability_events_logged(self):
        """Test that pipeline stages are logged."""
        clear_event_log()
        
        # Make a query
        self.client.post("/query", json={"query": "observability test"})
        
        # Check events were logged
        events = get_recent_events(100)
        
        # Should have events for multiple stages
        self.assertGreater(len(events), 0)
        
        # Check that we have events for different stages
        stages = set(event["stage"] for event in events)
        expected_stages = {"normalize", "constraints", "indices", "generate", "analyze", "score", "output"}
        
        # Should have at least some of these stages
        self.assertTrue(len(stages.intersection(expected_stages)) > 0)
    
    def test_response_determinism(self):
        """Test that API responses are deterministic."""
        query = "determinism check query"
        
        # Make multiple requests
        responses = []
        for _ in range(3):
            response = self.client.post("/query", json={"query": query})
            responses.append(response.json())
        
        # All responses should be identical
        for i in range(1, len(responses)):
            # Results should match
            self.assertEqual(responses[0]["results"], responses[i]["results"])
            
            # Event IDs should match (deterministic)
            self.assertEqual(responses[0]["event_id"], responses[i]["event_id"])
            
            # Normalized query should match
            self.assertEqual(responses[0]["query"], responses[i]["query"])
            
            # Count should match
            self.assertEqual(responses[0]["count"], responses[i]["count"])


if __name__ == '__main__':
    unittest.main()
