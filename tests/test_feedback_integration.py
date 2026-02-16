"""
Integration Tests for Feedback System

Tests the complete feedback loop including submission, retrieval,
query suggestions, and performance analysis.
"""

import unittest
from fastapi.testclient import TestClient
from api import app
from feedback import get_feedback_store


class TestFeedbackIntegration(unittest.TestCase):
    """Integration tests for feedback system."""

    def setUp(self):
        """Set up test client and clear feedback store."""
        self.client = TestClient(app)
        store = get_feedback_store()
        # Clear feedback data for tests
        store._feedback.clear()

    def test_feedback_submission_flow(self):
        """Test complete feedback submission flow."""
        # 1. Submit a query
        query = "artificial intelligence"
        response = self.client.post("/query", json={"query": query})
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 2. Get first result
        first_result = data["results"][0]
        result_sequence = first_result["sequence"]

        # 3. Submit feedback for the result
        feedback_data = {
            "query": query,
            "result_sequence": result_sequence,
            "rating": 5,
            "user_id": "test_user",
            "comment": "Excellent result!"
        }

        feedback_response = self.client.post("/feedback", json=feedback_data)
        self.assertEqual(feedback_response.status_code, 200)

        feedback_result = feedback_response.json()
        self.assertTrue(feedback_result["success"])
        self.assertIn("timestamp", feedback_result)

    def test_feedback_statistics_after_submissions(self):
        """Test feedback statistics aggregation."""
        # Submit multiple feedback entries
        queries_and_ratings = [
            ("quantum computing", 5),
            ("quantum computing", 4),
            ("machine learning", 3),
            ("machine learning", 5),
            ("neural networks", 2),
        ]

        for query, rating in queries_and_ratings:
            # Get result first
            response = self.client.post("/query", json={"query": query})
            result = response.json()["results"][0]

            # Submit feedback
            self.client.post("/feedback", json={
                "query": query,
                "result_sequence": result["sequence"],
                "rating": rating
            })

        # Get statistics
        stats_response = self.client.get("/feedback/stats")
        self.assertEqual(stats_response.status_code, 200)

        stats = stats_response.json()
        self.assertEqual(stats["total_feedback"], 5)
        self.assertEqual(stats["unique_queries"], 3)
        self.assertGreater(stats["average_rating"], 0)

    def test_query_suggestions_based_on_feedback(self):
        """Test query suggestions from feedback history."""
        # Submit feedback for related queries
        related_queries = [
            "quantum computing",
            "quantum mechanics",
            "quantum theory",
        ]

        for query in related_queries:
            response = self.client.post("/query", json={"query": query})
            result = response.json()["results"][0]

            self.client.post("/feedback", json={
                "query": query,
                "result_sequence": result["sequence"],
                "rating": 5
            })

        # Get suggestions for similar query
        suggestions_response = self.client.get(
            "/suggestions",
            params={"query": "quantum physics"}
        )
        self.assertEqual(suggestions_response.status_code, 200)

        suggestions = suggestions_response.json()
        self.assertIn("suggestions", suggestions)
        self.assertGreater(len(suggestions["suggestions"]), 0)

        # Suggestions should have related queries
        suggested_queries = [s["suggested_query"] for s in suggestions["suggestions"]]
        self.assertTrue(
            any("quantum" in q.lower() for q in suggested_queries)
        )

    def test_query_performance_analysis(self):
        """Test query performance analysis based on feedback."""
        query = "deep learning"

        # Submit positive feedback
        for i in range(3):
            response = self.client.post("/query", json={"query": query})
            result = response.json()["results"][0]

            self.client.post("/feedback", json={
                "query": query,
                "result_sequence": result["sequence"],
                "rating": 5
            })

        # Get performance analysis
        perf_response = self.client.get(
            "/query/performance",
            params={"query": query}
        )
        self.assertEqual(perf_response.status_code, 200)

        performance = perf_response.json()
        self.assertEqual(performance["query"], query)
        self.assertEqual(performance["total_feedback"], 3)
        self.assertEqual(performance["average_rating"], 5.0)
        self.assertEqual(performance["positive_ratio"], 100.0)

    def test_feedback_with_low_ratings_affects_suggestions(self):
        """Test that low-rated queries affect suggestions."""
        # Submit low-rated feedback
        low_query = "bad query example"
        response = self.client.post("/query", json={"query": low_query})
        result = response.json()["results"][0]

        self.client.post("/feedback", json={
            "query": low_query,
            "result_sequence": result["sequence"],
            "rating": 1
        })

        # Submit high-rated feedback
        good_query = "good query example"
        response = self.client.post("/query", json={"query": good_query})
        result = response.json()["results"][0]

        self.client.post("/feedback", json={
            "query": good_query,
            "result_sequence": result["sequence"],
            "rating": 5
        })

        # Suggestions should prioritize high-rated queries
        suggestions_response = self.client.get(
            "/suggestions",
            params={"query": "example query"}
        )

        suggestions = suggestions_response.json()["suggestions"]
        if len(suggestions) > 0:
            # First suggestion should have higher rating
            first_suggestion = suggestions[0]
            self.assertGreaterEqual(first_suggestion["average_rating"], 3.0)

    def test_feedback_invalid_rating(self):
        """Test that invalid ratings are rejected."""
        query = "test query"
        response = self.client.post("/query", json={"query": query})
        result = response.json()["results"][0]

        # Try invalid rating (too high)
        response = self.client.post("/feedback", json={
            "query": query,
            "result_sequence": result["sequence"],
            "rating": 10  # Invalid: must be 1-5
        })
        self.assertEqual(response.status_code, 422)  # Validation error

    def test_feedback_comment_length_limit(self):
        """Test that comment length limit is enforced."""
        query = "comment test"
        response = self.client.post("/query", json={"query": query})
        result = response.json()["results"][0]

        # Try very long comment
        long_comment = "x" * 1000  # Too long (max 500)

        response = self.client.post("/feedback", json={
            "query": query,
            "result_sequence": result["sequence"],
            "rating": 5,
            "comment": long_comment
        })
        self.assertEqual(response.status_code, 422)  # Validation error

    def test_feedback_for_multiple_results(self):
        """Test submitting feedback for multiple results."""
        query = "multiple results test"
        response = self.client.post("/query", json={"query": query})
        self.assertEqual(response.status_code, 200)

        results = response.json()["results"]

        # Submit feedback for each result
        for i, result in enumerate(results):
            feedback_response = self.client.post("/feedback", json={
                "query": query,
                "result_sequence": result["sequence"],
                "rating": i + 1  # Different ratings
            })
            self.assertEqual(feedback_response.status_code, 200)

        # Check statistics
        stats_response = self.client.get("/feedback/stats")
        stats = stats_response.json()
        self.assertEqual(stats["total_feedback"], len(results))

    def test_feedback_persistence_across_queries(self):
        """Test that feedback persists across different queries."""
        # Submit feedback for first query
        query1 = "persistence test 1"
        response1 = self.client.post("/query", json={"query": query1})
        result1 = response1.json()["results"][0]

        self.client.post("/feedback", json={
            "query": query1,
            "result_sequence": result1["sequence"],
            "rating": 5
        })

        # Submit different query
        query2 = "persistence test 2"
        response2 = self.client.post("/query", json={"query": query2})
        result2 = response2.json()["results"][0]

        self.client.post("/feedback", json={
            "query": query2,
            "result_sequence": result2["sequence"],
            "rating": 4
        })

        # Check that both feedbacks exist
        stats = self.client.get("/feedback/stats").json()
        self.assertEqual(stats["unique_queries"], 2)
        self.assertEqual(stats["total_feedback"], 2)

    def test_versioned_feedback_endpoints(self):
        """Test that versioned feedback endpoints work."""
        query = "version test"
        response = self.client.post("/query", json={"query": query})
        result = response.json()["results"][0]

        feedback_data = {
            "query": query,
            "result_sequence": result["sequence"],
            "rating": 5
        }

        # Test v2 endpoint
        v2_response = self.client.post("/v2/feedback", json=feedback_data)
        self.assertEqual(v2_response.status_code, 200)
        self.assertTrue(v2_response.json()["success"])


class TestFeedbackDeterminism(unittest.TestCase):
    """Test deterministic behavior of feedback system."""

    def setUp(self):
        """Set up test client and clear feedback store."""
        self.client = TestClient(app)
        store = get_feedback_store()
        store._feedback.clear()

    def test_identical_feedback_queries_same_suggestions(self):
        """Test that identical feedback produces same suggestions."""
        # Submit same feedback multiple times
        query = "determinism test"
        response = self.client.post("/query", json={"query": query})
        result = response.json()["results"][0]

        for _ in range(3):
            self.client.post("/feedback", json={
                "query": query,
                "result_sequence": result["sequence"],
                "rating": 5
            })

        # Get suggestions multiple times
        suggestions1 = self.client.get(
            "/suggestions",
            params={"query": "test"}
        ).json()

        suggestions2 = self.client.get(
            "/suggestions",
            params={"query": "test"}
        ).json()

        # Should be identical
        self.assertEqual(suggestions1, suggestions2)

    def test_performance_analysis_deterministic(self):
        """Test that performance analysis is deterministic."""
        query = "performance determinism"
        response = self.client.post("/query", json={"query": query})
        result = response.json()["results"][0]

        # Submit feedback
        self.client.post("/feedback", json={
            "query": query,
            "result_sequence": result["sequence"],
            "rating": 4
        })

        # Get performance multiple times
        perf1 = self.client.get(
            "/query/performance",
            params={"query": query}
        ).json()

        perf2 = self.client.get(
            "/query/performance",
            params={"query": query}
        ).json()

        # Should be identical
        self.assertEqual(perf1, perf2)


if __name__ == '__main__':
    unittest.main()
