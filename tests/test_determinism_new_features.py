"""
Determinism Tests for New Features

Tests that new authentication, versioning, and feedback features maintain determinism.
"""

import unittest
from fastapi.testclient import TestClient
from api import app
from auth import AuthService
from feedback import get_feedback_store


class TestAuthenticationDeterminism(unittest.TestCase):
    """Test deterministic behavior of authentication system."""

    def setUp(self):
        """Set up test fixtures."""
        self.auth = AuthService()
        self.client = TestClient(app)

    def test_same_credentials_same_token_structure(self):
        """Test that authentication is consistent."""
        username = "dettest"
        password = "detpass"

        # Create user
        self.auth.create_user(username, password)

        # Authenticate multiple times
        user1 = self.auth.authenticate_user(username, password)
        user2 = self.auth.authenticate_user(username, password)
        user3 = self.auth.authenticate_user(username, password)

        # Should return identical user objects
        self.assertEqual(user1.username, user2.username)
        self.assertEqual(user2.username, user3.username)
        self.assertEqual(user1.roles, user2.roles)
        self.assertEqual(user2.roles, user3.roles)

    def test_token_verification_deterministic(self):
        """Test that token verification is deterministic."""
        data = {"sub": "testuser", "roles": ["user"]}
        token = self.auth.create_access_token(data)

        # Verify multiple times
        result1 = self.auth.verify_token(token, token_type="access")
        result2 = self.auth.verify_token(token, token_type="access")
        result3 = self.auth.verify_token(token, token_type="access")

        # Should return identical data
        self.assertEqual(result1.username, result2.username)
        self.assertEqual(result2.username, result3.username)
        self.assertEqual(result1.roles, result2.roles)
        self.assertEqual(result2.roles, result3.roles)

    def test_password_hashing_deterministic_verification(self):
        """Test that password verification is deterministic."""
        password = "test_password"
        hashed = self.auth.get_password_hash(password)

        # Verify multiple times
        results = [self.auth.verify_password(password, hashed) for _ in range(10)]

        # All should be True
        self.assertTrue(all(results))

    def test_user_retrieval_deterministic(self):
        """Test that user retrieval is deterministic."""
        username = "retrievetest"
        self.auth.create_user(username, "pass", roles=["user", "admin"])

        # Retrieve multiple times
        user1 = self.auth.get_user(username)
        user2 = self.auth.get_user(username)
        user3 = self.auth.get_user(username)

        # Should be identical
        self.assertEqual(user1.username, user2.username)
        self.assertEqual(user1.roles, user2.roles)
        self.assertEqual(user2.username, user3.username)
        self.assertEqual(user2.roles, user3.roles)


class TestVersioningDeterminism(unittest.TestCase):
    """Test deterministic behavior of API versioning."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_version_info_deterministic(self):
        """Test that version info endpoint returns consistent data."""
        # Call multiple times
        responses = [self.client.get("/api/version") for _ in range(5)]

        # All should succeed
        for response in responses:
            self.assertEqual(response.status_code, 200)

        # All should return identical data
        data_list = [r.json() for r in responses]
        first_data = data_list[0]

        for data in data_list[1:]:
            self.assertEqual(data, first_data)

    def test_versioned_query_endpoints_deterministic(self):
        """Test that v1 and v2 query endpoints return same results."""
        query = "determinism test"

        # Query through different versions
        response_v1 = self.client.post("/query", json={"query": query})
        response_v2 = self.client.post("/v2/query", json={"query": query})

        # Both should succeed
        self.assertEqual(response_v1.status_code, 200)
        self.assertEqual(response_v2.status_code, 200)

        # Should return identical results
        result_v1 = response_v1.json()
        result_v2 = response_v2.json()

        self.assertEqual(result_v1["query"], result_v2["query"])
        self.assertEqual(result_v1["results"], result_v2["results"])
        self.assertEqual(result_v1["count"], result_v2["count"])

    def test_versioned_health_endpoints_deterministic(self):
        """Test that versioned health endpoints are consistent."""
        # Call all versions
        response_base = self.client.get("/health")
        response_v1 = self.client.get("/v1/health")
        response_v2 = self.client.get("/v2/health")

        # All should succeed
        self.assertEqual(response_base.status_code, 200)
        self.assertEqual(response_v1.status_code, 200)
        self.assertEqual(response_v2.status_code, 200)

        # Should have same structure
        data_base = response_base.json()
        data_v1 = response_v1.json()
        data_v2 = response_v2.json()

        # Service name should be identical
        self.assertEqual(data_base["service"], data_v1["service"])
        self.assertEqual(data_v1["service"], data_v2["service"])

    def test_root_endpoint_deterministic(self):
        """Test that root endpoint returns consistent information."""
        responses = [self.client.get("/") for _ in range(5)]

        # All should return same data
        data_list = [r.json() for r in responses]
        first_data = data_list[0]

        for data in data_list[1:]:
            self.assertEqual(data["version"], first_data["version"])
            self.assertEqual(data["api_version"], first_data["api_version"])


class TestFeedbackDeterminism(unittest.TestCase):
    """Test deterministic behavior of feedback system."""

    def setUp(self):
        """Set up test client and clear feedback store."""
        self.client = TestClient(app)
        store = get_feedback_store()
        store._feedback.clear()

    def test_feedback_submission_deterministic(self):
        """Test that feedback submission is deterministic."""
        # Submit query
        query = "feedback determinism"
        response = self.client.post("/query", json={"query": query})
        result = response.json()["results"][0]

        # Submit identical feedback multiple times
        feedback_data = {
            "query": query,
            "result_sequence": result["sequence"],
            "rating": 5,
            "user_id": "test_user",
            "comment": "Test comment"
        }

        responses = [
            self.client.post("/feedback", json=feedback_data)
            for _ in range(3)
        ]

        # All should succeed
        for response in responses:
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["success"])

    def test_feedback_statistics_deterministic(self):
        """Test that statistics are deterministic for same data."""
        # Submit some feedback
        query = "stats determinism"
        response = self.client.post("/query", json={"query": query})
        result = response.json()["results"][0]

        self.client.post("/feedback", json={
            "query": query,
            "result_sequence": result["sequence"],
            "rating": 5
        })

        # Get statistics multiple times
        stats_responses = [self.client.get("/feedback/stats") for _ in range(5)]

        # All should return identical data
        stats_list = [r.json() for r in stats_responses]
        first_stats = stats_list[0]

        for stats in stats_list[1:]:
            self.assertEqual(stats, first_stats)

    def test_query_suggestions_deterministic(self):
        """Test that suggestions are deterministic."""
        # Submit feedback for related queries
        queries = ["quantum computing", "quantum mechanics"]

        for query in queries:
            response = self.client.post("/query", json={"query": query})
            result = response.json()["results"][0]

            self.client.post("/feedback", json={
                "query": query,
                "result_sequence": result["sequence"],
                "rating": 5
            })

        # Get suggestions multiple times
        suggestion_responses = [
            self.client.get("/suggestions", params={"query": "quantum physics"})
            for _ in range(5)
        ]

        # All should return identical suggestions
        suggestions_list = [r.json() for r in suggestion_responses]
        first_suggestions = suggestions_list[0]

        for suggestions in suggestions_list[1:]:
            self.assertEqual(suggestions, first_suggestions)

    def test_query_performance_analysis_deterministic(self):
        """Test that performance analysis is deterministic."""
        # Submit feedback
        query = "performance determinism"
        response = self.client.post("/query", json={"query": query})
        result = response.json()["results"][0]

        self.client.post("/feedback", json={
            "query": query,
            "result_sequence": result["sequence"],
            "rating": 4
        })

        # Get performance analysis multiple times
        perf_responses = [
            self.client.get("/query/performance", params={"query": query})
            for _ in range(5)
        ]

        # All should return identical data
        perf_list = [r.json() for r in perf_responses]
        first_perf = perf_list[0]

        for perf in perf_list[1:]:
            self.assertEqual(perf, first_perf)


class TestCrosFeatureDeterminism(unittest.TestCase):
    """Test determinism across multiple new features."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
        store = get_feedback_store()
        store._feedback.clear()

    def test_query_with_feedback_deterministic(self):
        """Test that queries with feedback remain deterministic."""
        query = "cross feature test"

        # First query
        response1 = self.client.post("/query", json={"query": query})
        result1 = response1.json()

        # Submit feedback
        self.client.post("/feedback", json={
            "query": query,
            "result_sequence": result1["results"][0]["sequence"],
            "rating": 5
        })

        # Query again after feedback
        response2 = self.client.post("/query", json={"query": query})
        result2 = response2.json()

        # Results should be identical (feedback doesn't affect query results)
        self.assertEqual(result1["query"], result2["query"])
        self.assertEqual(result1["results"], result2["results"])

    def test_versioned_endpoints_with_auth_deterministic(self):
        """Test that versioned endpoints remain deterministic."""
        query = "versioning determinism"

        # Query through different versions multiple times
        v1_responses = [
            self.client.post("/query", json={"query": query})
            for _ in range(3)
        ]

        v2_responses = [
            self.client.post("/v2/query", json={"query": query})
            for _ in range(3)
        ]

        # All v1 responses should be identical
        v1_results = [r.json() for r in v1_responses]
        for result in v1_results[1:]:
            self.assertEqual(result, v1_results[0])

        # All v2 responses should be identical
        v2_results = [r.json() for r in v2_responses]
        for result in v2_results[1:]:
            self.assertEqual(result, v2_results[0])

        # v1 and v2 should return same results
        self.assertEqual(v1_results[0], v2_results[0])

    def test_metrics_dont_affect_determinism(self):
        """Test that metrics collection doesn't affect determinism."""
        query = "metrics determinism"

        # Submit multiple queries
        responses = [
            self.client.post("/query", json={"query": query})
            for _ in range(5)
        ]

        # All should return identical results
        results = [r.json() for r in responses]
        first_result = results[0]

        for result in results[1:]:
            self.assertEqual(result["results"], first_result["results"])

        # Check that metrics were collected
        metrics_response = self.client.get("/metrics")
        self.assertEqual(metrics_response.status_code, 200)
        self.assertIn("mnn_queries_total", metrics_response.text)

    def test_health_checks_dont_affect_query_determinism(self):
        """Test that health checks don't affect query determinism."""
        query = "health check determinism"

        # Query, health check, query again
        response1 = self.client.post("/query", json={"query": query})
        self.client.get("/health")
        response2 = self.client.post("/query", json={"query": query})

        # Results should be identical
        self.assertEqual(response1.json()["results"], response2.json()["results"])


class TestDeterminismUnderLoad(unittest.TestCase):
    """Test that determinism holds under concurrent load."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_concurrent_identical_queries_deterministic(self):
        """Test determinism with concurrent identical queries."""
        import concurrent.futures

        query = "concurrent determinism"

        # Submit concurrent identical queries
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(self.client.post, "/query", json={"query": query})
                for _ in range(20)
            ]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        self.assertTrue(all(r.status_code == 200 for r in responses))

        # All should return identical results
        results = [r.json()["results"] for r in responses]
        first_result = results[0]

        for result in results[1:]:
            self.assertEqual(result, first_result)

    def test_concurrent_mixed_queries_deterministic(self):
        """Test that different concurrent queries are deterministic."""
        import concurrent.futures

        queries = [f"concurrent mixed {i}" for i in range(5)]

        def query_twice(query):
            """Submit same query twice and verify results match."""
            r1 = self.client.post("/query", json={"query": query})
            r2 = self.client.post("/query", json={"query": query})
            return r1.json()["results"] == r2.json()["results"]

        # Submit concurrent queries
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(query_twice, q) for q in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All queries should have deterministic results
        self.assertTrue(all(results))


if __name__ == '__main__':
    unittest.main()
