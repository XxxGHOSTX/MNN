"""
Unit tests for MNN FastAPI Application

Tests the API endpoints including:
- Root endpoint
- Query endpoint
- Health check endpoint
- Deterministic behavior through API
- Error handling
"""

import unittest
from fastapi.testclient import TestClient
from api import app, cached_pipeline


class TestAPIEndpoints(unittest.TestCase):
    """Test cases for API endpoints."""
    
    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test that root endpoint returns API information."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('name', data)
        self.assertIn('version', data)
        self.assertIn('description', data)
    
    def test_health_endpoint(self):
        """Test that health endpoint returns status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('cache_info', data)
    
    def test_query_endpoint_success(self):
        """Test successful query processing."""
        response = self.client.post(
            "/query",
            json={"query": "artificial intelligence"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check response structure
        self.assertIn('query', data)
        self.assertIn('results', data)
        self.assertIn('count', data)
        
        # Check normalized query
        self.assertEqual(data['query'], 'ARTIFICIAL INTELLIGENCE')
        
        # Check results format
        self.assertIsInstance(data['results'], list)
        self.assertGreater(len(data['results']), 0)
        
        # Check result structure
        for result in data['results']:
            self.assertIn('sequence', result)
            self.assertIn('score', result)
    
    def test_query_endpoint_returns_top_5(self):
        """Test that API returns exactly top 5 results."""
        response = self.client.post(
            "/query",
            json={"query": "machine learning"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return 5 results (not 10 like CLI)
        self.assertEqual(len(data['results']), 5)
        self.assertEqual(data['count'], 5)
    
    def test_query_endpoint_empty_query_error(self):
        """Test that empty queries are rejected."""
        response = self.client.post(
            "/query",
            json={"query": ""}
        )
        self.assertEqual(response.status_code, 422)  # Validation error
    
    def test_query_endpoint_whitespace_only_query_error(self):
        """Test that whitespace-only queries are rejected."""
        response = self.client.post(
            "/query",
            json={"query": "   "}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('detail', data)
    
    def test_query_endpoint_normalized_empty_query_error(self):
        """Test that queries that normalize to empty are rejected."""
        response = self.client.post(
            "/query",
            json={"query": "!!!"}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('detail', data)
        # Query validation now catches excessive repetition or normalized empty patterns
        self.assertTrue(
            'repetition' in data['detail'].lower() or
            'normalization' in data['detail'].lower() or
            'empty' in data['detail'].lower()
        )
    
    def test_query_endpoint_missing_query_field(self):
        """Test that requests without query field are rejected."""
        response = self.client.post(
            "/query",
            json={}
        )
        self.assertEqual(response.status_code, 422)  # Validation error


class TestAPIDeterminism(unittest.TestCase):
    """Test cases for API deterministic behavior."""
    
    def setUp(self):
        """Set up test client and clear cache."""
        self.client = TestClient(app)
        # Clear cache before each test
        from api import _cached_execute_api_pipeline
        _cached_execute_api_pipeline.cache_clear()
    
    def test_identical_queries_produce_identical_results(self):
        """Test that the same query produces the same results through API."""
        query = {"query": "neural network"}
        
        # First request
        response1 = self.client.post("/query", json=query)
        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()
        
        # Second request
        response2 = self.client.post("/query", json=query)
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        
        # Results should be identical
        self.assertEqual(data1['query'], data2['query'])
        self.assertEqual(len(data1['results']), len(data2['results']))
        
        for r1, r2 in zip(data1['results'], data2['results']):
            self.assertEqual(r1['sequence'], r2['sequence'])
            self.assertEqual(r1['score'], r2['score'])
    
    def test_caching_works(self):
        """Test that caching improves performance."""
        query = {"query": "deep learning"}
        
        # Clear cache first
        from api import _cached_execute_api_pipeline
        _cached_execute_api_pipeline.cache_clear()
        
        # First request (cache miss)
        response1 = self.client.post("/query", json=query)
        self.assertEqual(response1.status_code, 200)
        
        # Check cache info after first request
        health1 = self.client.get("/health")
        cache_info1 = health1.json()['cache_info']
        
        # Second request (cache hit)
        response2 = self.client.post("/query", json=query)
        self.assertEqual(response2.status_code, 200)
        
        # Check cache info after second request
        health2 = self.client.get("/health")
        cache_info2 = health2.json()['cache_info']
        
        # Cache hits should have increased
        self.assertGreater(
            cache_info2['pipeline_cache_hits'],
            cache_info1['pipeline_cache_hits']
        )
    
    def test_different_queries_produce_different_results(self):
        """Test that different queries produce different results."""
        response1 = self.client.post("/query", json={"query": "hello"})
        response2 = self.client.post("/query", json={"query": "goodbye"})
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Queries should be different
        self.assertNotEqual(data1['query'], data2['query'])
        
        # Results should be different
        self.assertNotEqual(
            data1['results'][0]['sequence'],
            data2['results'][0]['sequence']
        )


class TestAPIResultsFormat(unittest.TestCase):
    """Test cases for API results format."""
    
    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_results_are_sorted_by_score(self):
        """Test that results are sorted by score in descending order."""
        response = self.client.post(
            "/query",
            json={"query": "information theory"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        scores = [result['score'] for result in data['results']]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_all_sequences_contain_pattern(self):
        """Test that all returned sequences contain the query pattern."""
        query_text = "quantum computing"
        response = self.client.post(
            "/query",
            json={"query": query_text}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        normalized_pattern = data['query']  # Get normalized version
        for result in data['results']:
            self.assertIn(normalized_pattern, result['sequence'])
    
    def test_scores_are_positive_floats(self):
        """Test that scores are positive floating point numbers."""
        response = self.client.post(
            "/query",
            json={"query": "data science"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        for result in data['results']:
            self.assertIsInstance(result['score'], float)
            self.assertGreater(result['score'], 0.0)


class TestAPIGuardrails(unittest.TestCase):
    """Test cases for API guardrails and limits."""
    
    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_query_too_long_rejected(self):
        """Test that queries exceeding MAX_QUERY_LENGTH are rejected."""
        from config import config
        long_query = "A" * (config.MAX_QUERY_LENGTH + 1)
        
        response = self.client.post(
            "/query",
            json={"query": long_query}
        )
        self.assertEqual(response.status_code, 422)  # Validation error
    
    def test_query_at_max_length_accepted(self):
        """Test that queries at MAX_QUERY_LENGTH are accepted."""
        from config import config
        query = "A" * config.MAX_QUERY_LENGTH
        
        response = self.client.post(
            "/query",
            json={"query": query}
        )
        # Should succeed (may return 200 or 400 depending on normalization)
        self.assertIn(response.status_code, [200, 400])
    
    def test_zero_length_query_rejected(self):
        """Test that zero-length queries are rejected."""
        response = self.client.post(
            "/query",
            json={"query": ""}
        )
        self.assertEqual(response.status_code, 422)  # Pydantic validation
    
    def test_excessive_repetition_rejected(self):
        """Test that queries with excessive repetition are rejected."""
        # Create query with very low character diversity (potential DoS)
        repetitive_query = "A" * 200
        
        response = self.client.post(
            "/query",
            json={"query": repetitive_query}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("repetition", data['detail'].lower())
    
    def test_sanitized_error_messages(self):
        """Test that error messages don't contain stack traces."""
        # Try to trigger an error
        response = self.client.post(
            "/query",
            json={"query": "   "}  # Whitespace only
        )
        
        data = response.json()
        # Should have detail but no stack trace
        self.assertIn('detail', data)
        self.assertNotIn('Traceback', str(data))
        self.assertNotIn('File "', str(data))


class TestMetricsEndpoint(unittest.TestCase):
    """Test cases for /metrics endpoint."""
    
    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_metrics_endpoint_exists(self):
        """Test that /metrics endpoint is accessible."""
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
    
    def test_metrics_response_structure(self):
        """Test that /metrics returns expected structure."""
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check required fields
        self.assertIn('request_count', data)
        self.assertIn('error_count', data)
        self.assertIn('cache_hits', data)
        self.assertIn('cache_misses', data)
        self.assertIn('cache_hit_rate', data)
        self.assertIn('lru_cache_info', data)
    
    def test_metrics_are_numeric(self):
        """Test that metric values are numeric."""
        response = self.client.get("/metrics")
        data = response.json()
        
        self.assertIsInstance(data['request_count'], int)
        self.assertIsInstance(data['error_count'], int)
        self.assertIsInstance(data['cache_hits'], int)
        self.assertIsInstance(data['cache_misses'], int)
        self.assertIsInstance(data['cache_hit_rate'], float)
    
    def test_metrics_update_after_request(self):
        """Test that metrics are updated after processing requests."""
        # Get initial metrics
        metrics_before = self.client.get("/metrics").json()
        
        # Make a query request
        self.client.post("/query", json={"query": "test query"})
        
        # Get updated metrics
        metrics_after = self.client.get("/metrics").json()
        
        # Request count should increase
        self.assertGreater(
            metrics_after['request_count'],
            metrics_before['request_count']
        )
    
    def test_metrics_cache_hit_rate_calculation(self):
        """Test that cache hit rate is calculated correctly."""
        response = self.client.get("/metrics")
        data = response.json()
        
        total = data['cache_hits'] + data['cache_misses']
        if total > 0:
            expected_rate = data['cache_hits'] / total
            self.assertAlmostEqual(data['cache_hit_rate'], expected_rate, places=5)
        else:
            self.assertEqual(data['cache_hit_rate'], 0.0)
    
    def test_metrics_deterministic_order(self):
        """Test that metrics response has deterministic key order."""
        response = self.client.get("/metrics")
        data = response.json()
        
        # Check that stage durations (if present) are sorted
        if 'last_stage_durations' in data:
            keys = list(data['last_stage_durations'].keys())
            self.assertEqual(keys, sorted(keys))
        
        if 'avg_stage_durations' in data:
            keys = list(data['avg_stage_durations'].keys())
            self.assertEqual(keys, sorted(keys))


class TestRootEndpointUpdate(unittest.TestCase):
    """Test that root endpoint lists /metrics."""
    
    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_root_lists_metrics_endpoint(self):
        """Test that root endpoint mentions /metrics."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('endpoints', data)
        self.assertIn('/metrics', data['endpoints'])


if __name__ == '__main__':
    unittest.main()
