"""
Unit tests for MNN API endpoints.

Tests cover API routes, request/response formats, and error handling.
"""

import unittest
from fastapi.testclient import TestClient

from mnn.api import app


class TestAPI(unittest.TestCase):
    """Test MNN API endpoints."""
    
    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test root endpoint returns API info."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("name", data)
        self.assertIn("version", data)
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
    
    def test_query_endpoint_success(self):
        """Test successful query processing."""
        response = self.client.post(
            "/query",
            json={"query": "test"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("results", data)
        self.assertIn("count", data)
        self.assertIsInstance(data["results"], list)
        self.assertIsInstance(data["count"], int)
        self.assertGreater(data["count"], 0)
    
    def test_query_result_structure(self):
        """Test query result structure."""
        response = self.client.post(
            "/query",
            json={"query": "hello"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check result items
        for result in data["results"]:
            self.assertIn("sequence", result)
            self.assertIn("score", result)
            self.assertIsInstance(result["sequence"], str)
            self.assertIsInstance(result["score"], (int, float))
    
    def test_query_empty_string(self):
        """Test query with empty string after normalization."""
        response = self.client.post(
            "/query",
            json={"query": "!!!"}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
    
    def test_query_missing_field(self):
        """Test query with missing field."""
        response = self.client.post(
            "/query",
            json={}
        )
        self.assertEqual(response.status_code, 422)
    
    def test_query_determinism(self):
        """Test that same query returns identical results."""
        query = {"query": "determinism"}
        
        response1 = self.client.post("/query", json=query)
        response2 = self.client.post("/query", json=query)
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Results should be identical
        self.assertEqual(data1["count"], data2["count"])
        self.assertEqual(len(data1["results"]), len(data2["results"]))
        
        for r1, r2 in zip(data1["results"], data2["results"]):
            self.assertEqual(r1["sequence"], r2["sequence"])
            self.assertEqual(r1["score"], r2["score"])
    
    def test_query_different_inputs(self):
        """Test that different queries return different results."""
        response1 = self.client.post("/query", json={"query": "alpha"})
        response2 = self.client.post("/query", json={"query": "beta"})
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Results should differ
        self.assertNotEqual(
            [r["sequence"] for r in data1["results"]],
            [r["sequence"] for r in data2["results"]]
        )


if __name__ == '__main__':
    unittest.main()
