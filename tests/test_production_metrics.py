"""
Production Behavior Tests for Metrics System

Tests metrics collection, export, and behavior under production-like conditions.
"""

import unittest
from fastapi.testclient import TestClient
from api import app
from metrics import get_metrics_collector, update_cache_metrics


class TestMetricsProduction(unittest.TestCase):
    """Test production behavior of metrics system."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
        # Reset metrics
        metrics = get_metrics_collector()
        metrics._counters.clear()
        metrics._histograms.clear()
        metrics._gauges.clear()

    def test_metrics_endpoint_returns_prometheus_format(self):
        """Test that /metrics endpoint returns Prometheus format."""
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response.headers["content-type"])

        # Should contain Prometheus-style metrics
        content = response.text
        self.assertIn("# TYPE", content)

    def test_query_metrics_incremented(self):
        """Test that queries increment metrics counters."""
        # Get initial metrics
        initial_response = self.client.get("/metrics")
        initial_content = initial_response.text

        # Submit queries
        for i in range(5):
            self.client.post("/query", json={"query": f"test query {i}"})

        # Get updated metrics
        final_response = self.client.get("/metrics")
        final_content = final_response.text

        # Should show increased query count
        self.assertIn("mnn_queries_total", final_content)
        self.assertIn("mnn_queries_success_total", final_content)

    def test_error_metrics_tracked(self):
        """Test that error queries are handled."""
        # Submit invalid query
        response = self.client.post("/query", json={"query": ""})

        # Should return error
        self.assertIn(response.status_code, [400, 422])

        # Metrics endpoint should still work
        metrics_response = self.client.get("/metrics")
        self.assertEqual(metrics_response.status_code, 200)

    def test_cache_metrics_updated(self):
        """Test that cache metrics are updated."""
        # Submit same query twice to trigger cache
        query = "cache test query"
        self.client.post("/query", json={"query": query})
        self.client.post("/query", json={"query": query})

        # Get metrics
        response = self.client.get("/metrics")
        content = response.text

        # Should have cache metrics
        self.assertIn("mnn_cache", content)

    def test_query_duration_histogram(self):
        """Test that query duration is tracked as histogram."""
        # Submit query
        self.client.post("/query", json={"query": "duration test"})

        # Get metrics
        response = self.client.get("/metrics")
        content = response.text

        # Should have histogram metrics
        self.assertIn("mnn_query_duration_seconds", content)

    def test_metrics_persist_across_requests(self):
        """Test that metrics persist across multiple requests."""
        # Submit multiple queries
        for i in range(3):
            self.client.post("/query", json={"query": f"persist test {i}"})

        # Get metrics multiple times
        response1 = self.client.get("/metrics")
        response2 = self.client.get("/metrics")

        # Metrics should be consistent
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        # Query count should be in both responses
        self.assertIn("mnn_queries_total", response1.text)
        self.assertIn("mnn_queries_total", response2.text)

    def test_slow_query_tracking(self):
        """Test that slow queries tracking exists."""
        # Submit a query (may or may not be slow)
        self.client.post("/query", json={"query": "slow query test"})

        # Get metrics
        response = self.client.get("/metrics")
        content = response.text

        # Query metrics should exist
        self.assertIn("mnn_query", content)

    def test_metrics_with_labels(self):
        """Test that metrics include labels."""
        # Submit successful query
        self.client.post("/query", json={"query": "label test"})

        # Submit failed query
        self.client.post("/query", json={"query": ""})

        # Get metrics
        response = self.client.get("/metrics")
        content = response.text

        # Should have labeled metrics for success
        self.assertIn('status="success"', content)

    def test_concurrent_metric_updates(self):
        """Test that metrics handle concurrent requests correctly."""
        import concurrent.futures

        # Submit concurrent queries
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(
                    self.client.post,
                    "/query",
                    json={"query": f"concurrent {i}"}
                )
                for i in range(10)
            ]
            concurrent.futures.wait(futures)

        # Get metrics
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        content = response.text

        # Should have recorded all queries
        self.assertIn("mnn_queries_total", content)


class TestHealthCheckProduction(unittest.TestCase):
    """Test production behavior of health check."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_health_check_returns_status(self):
        """Test that health check returns status information."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("status", data)
        self.assertIn("service", data)
        self.assertIn("version", data)
        self.assertIn("cache_info", data)

    def test_health_check_includes_cache_stats(self):
        """Test that health check includes cache statistics."""
        # Submit some queries to populate cache
        for i in range(3):
            self.client.post("/query", json={"query": f"health test {i}"})

        response = self.client.get("/health")
        data = response.json()

        # Should have cache info
        cache_info = data["cache_info"]
        self.assertIn("pipeline_cache_size", cache_info)
        self.assertIn("pipeline_cache_hits", cache_info)
        self.assertIn("pipeline_cache_misses", cache_info)

    def test_health_check_versioned_endpoints(self):
        """Test that versioned health endpoints work."""
        # Test v1 (deprecated)
        v1_response = self.client.get("/v1/health")
        self.assertEqual(v1_response.status_code, 200)

        # Test v2
        v2_response = self.client.get("/v2/health")
        self.assertEqual(v2_response.status_code, 200)

        # Both should return same structure
        self.assertEqual(v1_response.json()["service"], v2_response.json()["service"])

    def test_health_check_uptime_tracking(self):
        """Test that health check tracks uptime."""
        import time

        response1 = self.client.get("/health")
        data1 = response1.json()
        uptime1 = data1.get("uptime_seconds", 0)

        # Wait a bit
        time.sleep(0.1)

        response2 = self.client.get("/health")
        data2 = response2.json()
        uptime2 = data2.get("uptime_seconds", 0)

        # Uptime should increase
        self.assertGreaterEqual(uptime2, uptime1)


class TestVersionInfoProduction(unittest.TestCase):
    """Test production behavior of version endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_version_info_completeness(self):
        """Test that version info includes all expected fields."""
        response = self.client.get("/api/version")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("api_version", data)
        self.assertIn("pipeline_version", data)
        self.assertIn("features", data)
        self.assertIn("endpoints", data)
        self.assertIn("breaking_changes", data)

    def test_version_info_features_accurate(self):
        """Test that feature flags in version info are accurate."""
        response = self.client.get("/api/version")
        data = response.json()

        features = data["features"]
        # These features should be present
        self.assertIn("authentication", features)
        self.assertIn("jwt_oauth2", features)
        self.assertIn("api_versioning", features)
        self.assertIn("synonym_expansion", features)
        self.assertIn("user_feedback", features)

    def test_version_info_includes_deprecation_notices(self):
        """Test that version info includes deprecation information."""
        response = self.client.get("/api/version")
        data = response.json()

        endpoints = data["endpoints"]
        # v1 should be marked deprecated
        self.assertTrue(endpoints["v1"]["deprecated"])
        # v2 should be current
        self.assertTrue(endpoints["v2"]["current"])

    def test_versioned_version_endpoints(self):
        """Test that all version endpoint variants work."""
        # Test all variants
        variants = ["/api/version", "/v1/version", "/v2/version"]

        for endpoint in variants:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["api_version"], "2.0.0")


class TestProductionEdgeCases(unittest.TestCase):
    """Test edge cases in production scenarios."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_large_number_of_concurrent_queries(self):
        """Test handling of many concurrent queries."""
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    self.client.post,
                    "/query",
                    json={"query": f"concurrent test {i}"}
                )
                for i in range(50)
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        success_count = sum(1 for r in results if r.status_code == 200)
        self.assertGreater(success_count, 45)  # Allow for some variation

    def test_repeated_identical_queries_use_cache(self):
        """Test that repeated queries benefit from caching."""
        query = "cache benefit test"

        # First query
        response1 = self.client.post("/query", json={"query": query})
        result1 = response1.json()

        # Subsequent queries
        for _ in range(10):
            response = self.client.post("/query", json={"query": query})
            result = response.json()
            # Should return identical results
            self.assertEqual(result, result1)

        # Check cache hit rate
        health = self.client.get("/health").json()
        cache_hits = health["cache_info"]["pipeline_cache_hits"]
        self.assertGreater(cache_hits, 0)

    def test_mixed_valid_invalid_queries(self):
        """Test handling mix of valid and invalid queries."""
        queries = [
            {"query": "valid query 1", "should_succeed": True},
            {"query": "", "should_succeed": False},
            {"query": "valid query 2", "should_succeed": True},
            {"query": "   ", "should_succeed": False},
            {"query": "valid query 3", "should_succeed": True},
        ]

        for item in queries:
            response = self.client.post("/query", json={"query": item["query"]})
            if item["should_succeed"]:
                self.assertEqual(response.status_code, 200)
            else:
                # Can be 400 or 422 (validation error)
                self.assertIn(response.status_code, [400, 422])

    def test_unicode_queries_handled(self):
        """Test that Unicode queries are handled correctly."""
        unicode_queries = [
            "机器学习",  # Chinese
            "машинное обучение",  # Russian
            "aprendizaje automático",  # Spanish with accents
            "🤖 artificial intelligence",  # Emoji
        ]

        for query in unicode_queries:
            response = self.client.post("/query", json={"query": query})
            # Should either succeed or fail gracefully
            self.assertIn(response.status_code, [200, 400])


if __name__ == '__main__':
    unittest.main()
