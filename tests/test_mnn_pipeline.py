"""
Unit tests for the deterministic MNN pipeline modules.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api import app
from fastapi.testclient import TestClient
from main import run_pipeline
from mnn_pipeline.constraint_generator import generate_constraints
from mnn_pipeline.index_mapper import map_constraints_to_indices
from mnn_pipeline.query_normalizer import normalize_query
from mnn_pipeline.scorer import score_and_rank


class TestPipelineModules(unittest.TestCase):
    """Tests for core pipeline utilities."""

    def test_normalize_query(self):
        """Non-alphanumeric characters are removed and text uppercased."""
        result = normalize_query("Hello,  World??")
        self.assertEqual(result, "HELLO WORLD")

    def test_generate_constraints(self):
        """Constraints reflect pattern length."""
        constraints = generate_constraints("ABC")
        self.assertEqual(constraints["pattern"], "ABC")
        self.assertEqual(constraints["min_length"], 3)
        self.assertEqual(constraints["max_length"], constraints["min_length"] + 50)

    def test_map_constraints_to_indices(self):
        """Index mapping uses the pattern length as step size."""
        constraints = {"pattern": "ABCD"}
        indices = map_constraints_to_indices(constraints)
        self.assertEqual(indices[:3], [0, 4, 8])
        self.assertEqual(indices[-1], 996)

    def test_run_pipeline_is_deterministic(self):
        """Pipeline output is deterministic for identical input."""
        first = run_pipeline("alpha beta")
        second = run_pipeline("alpha beta")
        self.assertEqual(first, second)
        self.assertTrue(first[0].startswith("BOOK"))
        self.assertIn("ALPHA BETA", first[0])


class TestScoring(unittest.TestCase):
    """Tests for the scorer utility."""

    def test_center_bias_scoring(self):
        """Sequences with centered pattern score higher."""
        constraints = {"pattern": "TEST"}
        seqs = ["xx TEST xx", "TEST xx xx"]
        ranked = score_and_rank(seqs, constraints)
        self.assertEqual(ranked[0], "xx TEST xx")


class TestAPI(unittest.TestCase):
    """Tests for the FastAPI endpoint."""

    def setUp(self):
        self.client = TestClient(app)

    def test_query_endpoint(self):
        """API returns normalized query and top 5 results."""
        response = self.client.post("/query", json={"query": "sample query"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["normalized_query"], "SAMPLE QUERY")
        self.assertLessEqual(len(data["results"]), 5)
        self.assertTrue(all("SAMPLE QUERY" in item for item in data["results"]))


if __name__ == "__main__":
    unittest.main()
