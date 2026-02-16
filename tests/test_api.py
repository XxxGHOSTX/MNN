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


if __name__ == '__main__':
    unittest.main()
