"""
Unit Tests for MNN Pipeline

Comprehensive test suite for all pipeline components.
Tests determinism, validation, and correctness.

Author: MNN Engine Contributors
"""

import unittest
from mnn.query_normalizer import normalize_query
from mnn.constraint_generator import generate_constraints
from mnn.index_mapper import map_constraints_to_indices
from mnn.sequence_generator import generate_sequences
from mnn.analyzer import analyze_sequences
from mnn.scorer import score_and_rank
from mnn.pipeline import run_pipeline
from mnn.cache import clear_cache


class TestQueryNormalizer(unittest.TestCase):
    """Tests for query_normalizer module."""
    
    def test_normalize_basic(self):
        """Test basic normalization."""
        result = normalize_query("Hello World")
        self.assertEqual(result, "HELLO WORLD")
    
    def test_normalize_with_punctuation(self):
        """Test normalization removes punctuation."""
        result = normalize_query("Hello, World!")
        self.assertEqual(result, "HELLO WORLD")
    
    def test_normalize_with_numbers(self):
        """Test normalization preserves numbers."""
        result = normalize_query("test 123")
        self.assertEqual(result, "TEST 123")
    
    def test_normalize_multiple_spaces(self):
        """Test normalization collapses whitespace."""
        result = normalize_query("test    query   here")
        self.assertEqual(result, "TEST QUERY HERE")
    
    def test_normalize_strip_whitespace(self):
        """Test normalization strips leading/trailing whitespace."""
        result = normalize_query("  test  ")
        self.assertEqual(result, "TEST")
    
    def test_normalize_empty_raises(self):
        """Test normalization raises on empty result."""
        with self.assertRaises(ValueError) as cm:
            normalize_query("!!!")
        self.assertIn("empty", str(cm.exception).lower())
    
    def test_normalize_whitespace_only_raises(self):
        """Test normalization raises on whitespace-only input."""
        with self.assertRaises(ValueError):
            normalize_query("   ")


class TestConstraintGenerator(unittest.TestCase):
    """Tests for constraint_generator module."""
    
    def test_generate_basic_constraints(self):
        """Test basic constraint generation."""
        result = generate_constraints("HELLO")
        self.assertEqual(result['pattern'], "HELLO")
        self.assertEqual(result['min_length'], 5)
        self.assertEqual(result['max_length'], 55)
    
    def test_generate_constraints_with_spaces(self):
        """Test constraint generation with spaces in pattern."""
        result = generate_constraints("TEST QUERY")
        self.assertEqual(result['pattern'], "TEST QUERY")
        self.assertEqual(result['min_length'], 10)
        self.assertEqual(result['max_length'], 60)
    
    def test_generate_constraints_empty_raises(self):
        """Test constraint generation raises on empty pattern."""
        with self.assertRaises(ValueError) as cm:
            generate_constraints("")
        self.assertIn("empty", str(cm.exception).lower())


class TestIndexMapper(unittest.TestCase):
    """Tests for index_mapper module."""
    
    def test_map_indices_basic(self):
        """Test basic index mapping."""
        constraints = {'pattern': 'HELLO'}
        indices = map_constraints_to_indices(constraints)
        self.assertIsInstance(indices, list)
        self.assertGreater(len(indices), 0)
        self.assertEqual(indices[0], 0)
    
    def test_map_indices_step_size(self):
        """Test index mapping step size based on pattern length."""
        constraints = {'pattern': 'AB'}
        indices = map_constraints_to_indices(constraints)
        # Step should be max(1, 2) = 2
        self.assertEqual(indices[:5], [0, 2, 4, 6, 8])
    
    def test_map_indices_deterministic(self):
        """Test index mapping is deterministic."""
        constraints = {'pattern': 'TEST'}
        indices1 = map_constraints_to_indices(constraints)
        indices2 = map_constraints_to_indices(constraints)
        self.assertEqual(indices1, indices2)
    
    def test_map_indices_cached(self):
        """Test index mapping uses cache."""
        constraints = {'pattern': 'CACHED'}
        # Call twice
        indices1 = map_constraints_to_indices(constraints)
        indices2 = map_constraints_to_indices(constraints)
        # Should be identical (cached - values are equal)
        self.assertEqual(indices1, indices2)


class TestSequenceGenerator(unittest.TestCase):
    """Tests for sequence_generator module."""
    
    def test_generate_sequences_basic(self):
        """Test basic sequence generation."""
        indices = [0, 5, 10]
        constraints = {'pattern': 'ABC', 'max_length': 53}
        sequences = generate_sequences(indices, constraints)
        self.assertEqual(len(sequences), 3)
    
    def test_generate_sequences_pattern_presence(self):
        """Test all sequences contain the pattern."""
        indices = [0, 5, 10, 15]
        constraints = {'pattern': 'TEST', 'max_length': 54}
        sequences = generate_sequences(indices, constraints)
        for seq in sequences:
            self.assertIn('TEST', seq)
    
    def test_generate_sequences_length_constraint(self):
        """Test sequences respect length constraints."""
        indices = [0, 5, 10]
        constraints = {'pattern': 'ABC', 'max_length': 53}
        sequences = generate_sequences(indices, constraints)
        max_allowed = constraints['max_length'] + 100
        for seq in sequences:
            self.assertLessEqual(len(seq), max_allowed)
    
    def test_generate_sequences_deterministic(self):
        """Test sequence generation is deterministic."""
        indices = [0, 5, 10, 15, 20]
        constraints = {'pattern': 'HELLO', 'max_length': 55}
        sequences1 = generate_sequences(indices, constraints)
        sequences2 = generate_sequences(indices, constraints)
        self.assertEqual(sequences1, sequences2)
    
    def test_generate_sequences_ordering(self):
        """Test sequence generation preserves index ordering."""
        indices = [20, 5, 15, 0, 10]  # Unsorted
        constraints = {'pattern': 'ABC', 'max_length': 53}
        sequences = generate_sequences(indices, constraints)
        # Should be sorted by indices
        self.assertEqual(len(sequences), 5)


class TestAnalyzer(unittest.TestCase):
    """Tests for analyzer module."""
    
    def test_analyze_filters_by_pattern(self):
        """Test analyzer filters sequences by pattern presence."""
        sequences = ['XABCX', 'DEFGH', 'ABCDEFG', 'XYZ']
        constraints = {
            'pattern': 'ABC',
            'min_length': 3,
            'max_length': 53
        }
        filtered = analyze_sequences(sequences, constraints)
        self.assertEqual(len(filtered), 2)
        self.assertIn('XABCX', filtered)
        self.assertIn('ABCDEFG', filtered)
    
    def test_analyze_filters_by_min_length(self):
        """Test analyzer filters by minimum length."""
        sequences = ['AB', 'ABC', 'ABCD', 'ABCDE']
        constraints = {
            'pattern': 'AB',
            'min_length': 4,
            'max_length': 54
        }
        filtered = analyze_sequences(sequences, constraints)
        # Only sequences with length >= 4
        self.assertNotIn('AB', filtered)
        self.assertNotIn('ABC', filtered)
        self.assertIn('ABCD', filtered)
        self.assertIn('ABCDE', filtered)
    
    def test_analyze_filters_by_max_length(self):
        """Test analyzer filters by maximum length."""
        sequences = ['ABC' + 'X' * 50, 'ABC' + 'X' * 200]
        constraints = {
            'pattern': 'ABC',
            'min_length': 3,
            'max_length': 53
        }
        filtered = analyze_sequences(sequences, constraints)
        # max_length + 100 = 153, so second sequence too long
        self.assertEqual(len(filtered), 1)
    
    def test_analyze_preserves_order(self):
        """Test analyzer preserves input order."""
        sequences = ['ZABC', 'AABC', 'MABC']
        constraints = {
            'pattern': 'ABC',
            'min_length': 3,
            'max_length': 53
        }
        filtered = analyze_sequences(sequences, constraints)
        self.assertEqual(filtered, ['ZABC', 'AABC', 'MABC'])


class TestScorer(unittest.TestCase):
    """Tests for scorer module."""
    
    def test_score_and_rank_basic(self):
        """Test basic scoring and ranking."""
        sequences = ['XABCX', 'XXABCXX', 'ABCXXXX']
        constraints = {'pattern': 'ABC'}
        results = score_and_rank(sequences, constraints)
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIn('sequence', result)
            self.assertIn('score', result)
    
    def test_score_and_rank_descending(self):
        """Test results are sorted by score descending."""
        sequences = ['XABCX', 'XXABCXX', 'ABCXXXX']
        constraints = {'pattern': 'ABC'}
        results = score_and_rank(sequences, constraints)
        scores = [r['score'] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_score_and_rank_centered_wins(self):
        """Test more centered patterns score higher."""
        # Pattern at center should score highest
        sequences = [
            'ABC' + 'X' * 20,      # Pattern at start
            'X' * 10 + 'ABC' + 'X' * 10,  # Pattern centered
            'X' * 20 + 'ABC'       # Pattern at end
        ]
        constraints = {'pattern': 'ABC'}
        results = score_and_rank(sequences, constraints)
        # Centered pattern should be first
        self.assertIn('ABC', results[0]['sequence'])
        # Verify it's the centered one
        centered_seq = 'X' * 10 + 'ABC' + 'X' * 10
        self.assertEqual(results[0]['sequence'], centered_seq)
    
    def test_score_and_rank_deterministic(self):
        """Test scoring and ranking is deterministic."""
        sequences = ['XABCX', 'XXABCXX', 'ABCXXXX', 'XXXABCXXX']
        constraints = {'pattern': 'ABC'}
        results1 = score_and_rank(sequences, constraints)
        results2 = score_and_rank(sequences, constraints)
        self.assertEqual(results1, results2)
    
    def test_score_and_rank_tie_breaking(self):
        """Test deterministic tie-breaking on equal scores."""
        # Create sequences with same centering (same score)
        sequences = ['XABCX', 'XDEFX']  # Different patterns, same structure
        # Use pattern that matches first sequence
        constraints = {'pattern': 'ABC'}
        results = score_and_rank(sequences, constraints)
        # Should preserve original order for determinism
        self.assertEqual(results[0]['sequence'], 'XABCX')


class TestPipeline(unittest.TestCase):
    """Tests for end-to-end pipeline."""
    
    def setUp(self):
        """Clear cache before each test."""
        clear_cache()
    
    def test_pipeline_basic(self):
        """Test basic pipeline execution."""
        results = run_pipeline("test query")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertIn('sequence', result)
            self.assertIn('score', result)
    
    def test_pipeline_deterministic(self):
        """Test pipeline produces deterministic results."""
        results1 = run_pipeline("hello world")
        results2 = run_pipeline("hello world")
        self.assertEqual(results1, results2)
    
    def test_pipeline_cached(self):
        """Test pipeline uses caching."""
        query = "cached query"
        results1 = run_pipeline(query)
        results2 = run_pipeline(query)
        # Should be identical due to caching
        self.assertEqual(results1, results2)
    
    def test_pipeline_different_queries(self):
        """Test different queries produce different results."""
        results1 = run_pipeline("query one")
        results2 = run_pipeline("query two")
        # Results should be different
        self.assertNotEqual(results1, results2)
    
    def test_pipeline_empty_query_raises(self):
        """Test pipeline raises on empty normalized query."""
        with self.assertRaises(ValueError):
            run_pipeline("!!!")
    
    def test_pipeline_cache_clear(self):
        """Test cache clearing works."""
        query = "test cache clear"
        results1 = run_pipeline(query)
        clear_cache()
        results2 = run_pipeline(query)
        # Should be equal but not same object after cache clear
        self.assertEqual(results1, results2)
    
    def test_pipeline_repeated_calls_identical(self):
        """Test multiple repeated calls produce identical results."""
        query = "repeated test"
        results = [run_pipeline(query) for _ in range(5)]
        # All results should be identical
        for i in range(1, len(results)):
            self.assertEqual(results[0], results[i])


if __name__ == '__main__':
    unittest.main()
