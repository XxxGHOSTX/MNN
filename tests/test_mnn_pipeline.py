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
from mnn_pipeline.analyzer import analyze_sequences
from mnn_pipeline.constraint_generator import generate_constraints
from mnn_pipeline.index_mapper import map_constraints_to_indices
from mnn_pipeline.query_normalizer import normalize_query
from mnn_pipeline.sequence_generator import generate_sequences
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
        self.assertTrue(first[0]["sequence"].startswith("BOOK"))
        self.assertIn("ALPHA BETA", first[0]["sequence"])

    def test_sequence_generation_and_analysis(self):
        """Generated sequences respect constraints and are filtered deterministically."""
        constraints = generate_constraints("PATTERN")
        indices = [0, 7, 14]
        generated = generate_sequences(indices, constraints)
        # All sequences should include the pattern and carry indices
        self.assertTrue(all("PATTERN" in seq for _, seq in generated))

        filtered = analyze_sequences(generated, constraints)
        self.assertEqual(generated, filtered)  # All sequences valid under constraints


class TestScoring(unittest.TestCase):
    """Tests for the scorer utility."""

    def test_center_bias_scoring(self):
        """Sequences with centered pattern score higher."""
        constraints = {"pattern": "TEST", "min_length": 0, "max_length": 50}
        seqs = [(1, "xx TEST xx"), (2, "TEST xx xx")]
        ranked = score_and_rank(seqs, constraints)
        self.assertEqual(ranked[0]["sequence"], "xx TEST xx")
        self.assertGreaterEqual(ranked[0]["score"], ranked[1]["score"])


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
        self.assertTrue(all("sequence" in item and "score" in item for item in data["results"]))
        self.assertTrue(all("SAMPLE QUERY" in item["sequence"] for item in data["results"]))


if __name__ == "__main__":
    unittest.main()
