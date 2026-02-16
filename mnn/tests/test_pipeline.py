"""
Unit tests for MNN pipeline modules.

Tests cover normalization, constraints, mapping, generation, analysis,
scoring, and full pipeline determinism.
"""

import unittest
from mnn.query_normalizer import normalize_query
from mnn.constraint_generator import generate_constraints
from mnn.index_mapper import map_constraints_to_indices
from mnn.sequence_generator import generate_sequences
from mnn.analyzer import analyze_sequences
from mnn.scorer import score_and_rank
from mnn.pipeline import run_pipeline


class TestQueryNormalizer(unittest.TestCase):
    """Test query normalization."""
    
    def test_basic_normalization(self):
        """Test basic query normalization."""
        result = normalize_query("Hello World!")
        self.assertEqual(result, "HELLO WORLD")
    
    def test_whitespace_collapse(self):
        """Test whitespace collapsing."""
        result = normalize_query("  test   query  ")
        self.assertEqual(result, "TEST QUERY")
    
    def test_special_characters_removed(self):
        """Test special character removal."""
        result = normalize_query("test@#$%query")
        self.assertEqual(result, "TESTQUERY")
    
    def test_empty_after_normalization(self):
        """Test ValueError raised for empty normalized query."""
        with self.assertRaises(ValueError):
            normalize_query("!!!@@@###")
    
    def test_only_whitespace(self):
        """Test ValueError raised for whitespace-only query."""
        with self.assertRaises(ValueError):
            normalize_query("   ")
    
    def test_alphanumeric_preserved(self):
        """Test that alphanumeric characters are preserved."""
        result = normalize_query("Test123")
        self.assertEqual(result, "TEST123")


class TestConstraintGenerator(unittest.TestCase):
    """Test constraint generation."""
    
    def test_basic_constraints(self):
        """Test basic constraint generation."""
        constraints = generate_constraints("TEST")
        self.assertEqual(constraints['pattern'], "TEST")
        self.assertEqual(constraints['min_length'], 4)
        self.assertEqual(constraints['max_length'], 54)
    
    def test_single_char_pattern(self):
        """Test constraints for single character."""
        constraints = generate_constraints("A")
        self.assertEqual(constraints['pattern'], "A")
        self.assertEqual(constraints['min_length'], 1)
        self.assertEqual(constraints['max_length'], 51)
    
    def test_long_pattern(self):
        """Test constraints for long pattern."""
        pattern = "LONGPATTERN"
        constraints = generate_constraints(pattern)
        self.assertEqual(constraints['pattern'], pattern)
        self.assertEqual(constraints['min_length'], len(pattern))
        self.assertEqual(constraints['max_length'], len(pattern) + 50)


class TestIndexMapper(unittest.TestCase):
    """Test index mapping."""
    
    def test_basic_mapping(self):
        """Test basic index mapping."""
        constraints = {'pattern': 'TEST'}
        indices = map_constraints_to_indices(constraints)
        self.assertIsInstance(indices, list)
        self.assertTrue(all(isinstance(i, int) for i in indices))
        self.assertEqual(indices[0], 0)
        self.assertEqual(indices[1], 4)  # step = len("TEST")
    
    def test_single_char_step(self):
        """Test mapping with single character pattern."""
        constraints = {'pattern': 'A'}
        indices = map_constraints_to_indices(constraints)
        self.assertEqual(indices[0], 0)
        self.assertEqual(indices[1], 1)  # step = max(1, 1)
    
    def test_determinism(self):
        """Test that same pattern produces same indices."""
        constraints = {'pattern': 'TEST'}
        indices1 = map_constraints_to_indices(constraints)
        indices2 = map_constraints_to_indices(constraints)
        self.assertEqual(indices1, indices2)
    
    def test_range_bounds(self):
        """Test that indices are in range [0, 1000)."""
        constraints = {'pattern': 'AB'}
        indices = map_constraints_to_indices(constraints)
        self.assertTrue(all(0 <= i < 1000 for i in indices))


class TestSequenceGenerator(unittest.TestCase):
    """Test sequence generation."""
    
    def test_basic_generation(self):
        """Test basic sequence generation."""
        indices = [0, 4, 8]
        constraints = {'pattern': 'AB', 'max_length': 52}
        sequences = generate_sequences(indices, constraints)
        self.assertEqual(len(sequences), 3)
        self.assertTrue(all(isinstance(s, str) for s in sequences))
    
    def test_pattern_embedded(self):
        """Test that pattern is embedded in sequences."""
        indices = [0, 4]
        constraints = {'pattern': 'TEST', 'max_length': 54}
        sequences = generate_sequences(indices, constraints)
        for seq in sequences:
            self.assertIn('TEST', seq)
    
    def test_length_constraint(self):
        """Test sequence length constraint."""
        indices = [0, 4]
        constraints = {'pattern': 'TEST', 'max_length': 54}
        sequences = generate_sequences(indices, constraints)
        max_allowed = constraints['max_length'] + 100
        for seq in sequences:
            self.assertLessEqual(len(seq), max_allowed)
    
    def test_deterministic_order(self):
        """Test deterministic ordering."""
        indices = [8, 0, 4]  # Unsorted
        constraints = {'pattern': 'TEST', 'max_length': 54}
        sequences1 = generate_sequences(indices, constraints)
        sequences2 = generate_sequences(indices, constraints)
        self.assertEqual(sequences1, sequences2)


class TestAnalyzer(unittest.TestCase):
    """Test sequence analysis."""
    
    def test_pattern_filtering(self):
        """Test filtering by pattern presence."""
        sequences = ['XTEST', 'NOPE', 'TESTX']
        constraints = {'pattern': 'TEST', 'min_length': 4, 'max_length': 54}
        filtered = analyze_sequences(sequences, constraints)
        self.assertEqual(len(filtered), 2)
        self.assertIn('XTEST', filtered)
        self.assertIn('TESTX', filtered)
        self.assertNotIn('NOPE', filtered)
    
    def test_length_filtering(self):
        """Test filtering by length constraints."""
        sequences = ['TEST', 'T' * 200]  # Too long
        constraints = {'pattern': 'T', 'min_length': 1, 'max_length': 51}
        filtered = analyze_sequences(sequences, constraints)
        # max_length + 100 = 151, so 200 chars is too long
        self.assertIn('TEST', filtered)
        self.assertNotIn('T' * 200, filtered)
    
    def test_min_length_filtering(self):
        """Test minimum length filtering."""
        sequences = ['AB', 'ABC', 'ABCD']
        constraints = {'pattern': 'AB', 'min_length': 3, 'max_length': 52}
        filtered = analyze_sequences(sequences, constraints)
        self.assertNotIn('AB', filtered)  # Too short
        self.assertIn('ABC', filtered)
        self.assertIn('ABCD', filtered)


class TestScorer(unittest.TestCase):
    """Test scoring and ranking."""
    
    def test_basic_scoring(self):
        """Test basic sequence scoring."""
        sequences = ['XTESTX', 'XXXTESTXXX']
        constraints = {'pattern': 'TEST'}
        results = score_and_rank(sequences, constraints)
        self.assertEqual(len(results), 2)
        self.assertTrue(all('sequence' in r and 'score' in r for r in results))
    
    def test_score_calculation(self):
        """Test score calculation formula."""
        sequences = ['XTEST']  # Pattern at position 1
        constraints = {'pattern': 'TEST'}
        results = score_and_rank(sequences, constraints)
        
        # Verify score calculation
        seq = sequences[0]
        pattern_start = seq.find('TEST')
        center_seq = len(seq) / 2.0
        center_pattern = pattern_start + len('TEST') / 2.0
        expected_score = 1.0 / (1.0 + abs(center_seq - center_pattern))
        
        self.assertAlmostEqual(results[0]['score'], expected_score, places=5)
    
    def test_descending_order(self):
        """Test that results are sorted by score descending."""
        sequences = ['XTEST', 'XXTESTXX']  # Second is more centered
        constraints = {'pattern': 'TEST'}
        results = score_and_rank(sequences, constraints)
        
        # Scores should be descending
        for i in range(len(results) - 1):
            self.assertGreaterEqual(results[i]['score'], results[i + 1]['score'])
    
    def test_deterministic_tie_breaking(self):
        """Test deterministic tie-breaking."""
        # Create sequences with identical scores
        sequences = ['ATEST', 'BTEST']  # Same structure, different first char
        constraints = {'pattern': 'TEST'}
        results1 = score_and_rank(sequences, constraints)
        results2 = score_and_rank(sequences, constraints)
        
        # Order should be identical
        self.assertEqual(
            [r['sequence'] for r in results1],
            [r['sequence'] for r in results2]
        )


class TestPipeline(unittest.TestCase):
    """Test full pipeline."""
    
    def test_pipeline_executes(self):
        """Test that pipeline executes successfully."""
        results = run_pipeline("test")
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)
    
    def test_pipeline_result_structure(self):
        """Test pipeline result structure."""
        results = run_pipeline("test")
        for result in results:
            self.assertIn('sequence', result)
            self.assertIn('score', result)
            self.assertIsInstance(result['sequence'], str)
            self.assertIsInstance(result['score'], float)
    
    def test_pipeline_determinism(self):
        """Test that same query produces identical results."""
        results1 = run_pipeline("hello")
        results2 = run_pipeline("hello")
        
        self.assertEqual(len(results1), len(results2))
        for r1, r2 in zip(results1, results2):
            self.assertEqual(r1['sequence'], r2['sequence'])
            self.assertEqual(r1['score'], r2['score'])
    
    def test_pipeline_different_queries(self):
        """Test that different queries produce different results."""
        results1 = run_pipeline("hello")
        results2 = run_pipeline("world")
        
        # Results should be different
        self.assertNotEqual(
            [r['sequence'] for r in results1],
            [r['sequence'] for r in results2]
        )
    
    def test_pipeline_empty_query(self):
        """Test that empty query raises ValueError."""
        with self.assertRaises(ValueError):
            run_pipeline("!!!")
    
    def test_pipeline_cache(self):
        """Test that pipeline caching works."""
        # Clear cache first
        run_pipeline.cache_clear()
        
        # First call
        results1 = run_pipeline("cache test")
        cache_info1 = run_pipeline.cache_info()
        
        # Second call (should hit cache)
        results2 = run_pipeline("cache test")
        cache_info2 = run_pipeline.cache_info()
        
        # Results should be identical
        self.assertEqual(len(results1), len(results2))
        
        # Cache hits should increase
        self.assertEqual(cache_info2.hits, cache_info1.hits + 1)


if __name__ == '__main__':
    unittest.main()
