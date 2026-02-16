"""
API Integration Tests for MNN

Tests for FastAPI REST API endpoints.
Validates request/response handling and determinism.

Author: MNN Engine Contributors
"""

import unittest
from fastapi.testclient import TestClient
from mnn.api import app
from mnn.cache import clear_cache


class TestAPI(unittest.TestCase):
    """Tests for FastAPI endpoints."""
    
    def setUp(self):
        """Set up test client and clear cache."""
        self.client = TestClient(app)
        clear_cache()
    
    def test_root_endpoint(self):
        """Test root endpoint returns API info."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('name', data)
        self.assertIn('version', data)
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
    
    def test_query_endpoint_success(self):
        """Test successful query processing."""
        response = self.client.post(
            "/query",
            json={"query": "test query"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn('query', data)
        self.assertIn('normalized_query', data)
        self.assertIn('ranked', data)
        self.assertIn('count', data)
        
        # Verify data correctness
        self.assertEqual(data['query'], 'test query')
        self.assertEqual(data['normalized_query'], 'TEST QUERY')
        self.assertIsInstance(data['ranked'], list)
        self.assertEqual(data['count'], len(data['ranked']))
    
    def test_query_endpoint_result_structure(self):
        """Test query endpoint returns properly structured results."""
        response = self.client.post(
            "/query",
            json={"query": "hello world"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify ranked results structure
        self.assertGreater(len(data['ranked']), 0)
        for result in data['ranked']:
            self.assertIn('sequence', result)
            self.assertIn('score', result)
            self.assertIsInstance(result['sequence'], str)
            self.assertIsInstance(result['score'], float)
    
    def test_query_endpoint_empty_query(self):
        """Test query endpoint with empty query after normalization."""
        response = self.client.post(
            "/query",
            json={"query": "!!!"}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('detail', data)
        self.assertIn('empty', data['detail'].lower())
    
    def test_query_endpoint_whitespace_only(self):
        """Test query endpoint with whitespace-only query."""
        response = self.client.post(
            "/query",
            json={"query": "   "}
        )
        self.assertEqual(response.status_code, 400)
    
    def test_query_endpoint_deterministic(self):
        """Test query endpoint returns deterministic results."""
        query_data = {"query": "deterministic test"}
        
        response1 = self.client.post("/query", json=query_data)
        response2 = self.client.post("/query", json=query_data)
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Results should be identical
        self.assertEqual(data1['ranked'], data2['ranked'])
    
    def test_query_endpoint_multiple_calls(self):
        """Test multiple calls to query endpoint with same query."""
        query_data = {"query": "repeated query"}
        
        responses = [
            self.client.post("/query", json=query_data)
            for _ in range(5)
        ]
        
        # All should succeed
        for response in responses:
            self.assertEqual(response.status_code, 200)
        
        # All should return identical results
        results = [r.json()['ranked'] for r in responses]
        for i in range(1, len(results)):
            self.assertEqual(results[0], results[i])
    
    def test_query_endpoint_different_queries(self):
        """Test different queries produce different results."""
        response1 = self.client.post(
            "/query",
            json={"query": "first query"}
        )
        response2 = self.client.post(
            "/query",
            json={"query": "second query"}
        )
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Results should be different
        self.assertNotEqual(data1['ranked'], data2['ranked'])
    
    def test_query_endpoint_normalization(self):
        """Test query normalization in API response."""
        response = self.client.post(
            "/query",
            json={"query": "Hello, World! 123"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check normalization
        self.assertEqual(data['normalized_query'], 'HELLO WORLD 123')
    
    def test_query_endpoint_scores_descending(self):
        """Test query results are sorted by score descending."""
        response = self.client.post(
            "/query",
            json={"query": "test"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        scores = [result['score'] for result in data['ranked']]
        # Verify descending order
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i], scores[i + 1])
    
    def test_query_endpoint_all_sequences_contain_pattern(self):
        """Test all returned sequences contain the normalized pattern."""
        response = self.client.post(
            "/query",
            json={"query": "pattern"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        pattern = data['normalized_query']
        for result in data['ranked']:
            self.assertIn(pattern, result['sequence'])
    
    def test_query_endpoint_caching(self):
        """Test API caching behavior."""
        query_data = {"query": "cache test"}
        
        # First call - should execute pipeline
        response1 = self.client.post("/query", json=query_data)
        self.assertEqual(response1.status_code, 200)
        
        # Second call - should use cache
        response2 = self.client.post("/query", json=query_data)
        self.assertEqual(response2.status_code, 200)
        
        # Results should be identical
        self.assertEqual(response1.json(), response2.json())
        
        # Clear cache
        clear_cache()
        
        # Third call - should re-execute pipeline
        response3 = self.client.post("/query", json=query_data)
        self.assertEqual(response3.status_code, 200)
        
        # Should still be equal to previous results
        self.assertEqual(response1.json(), response3.json())


if __name__ == '__main__':
    unittest.main()
