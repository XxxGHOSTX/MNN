"""
Unit tests for MNN Pipeline modules

Tests the deterministic behavior of all pipeline stages including:
- Query normalization
- Constraint generation
- Index mapping
- Sequence generation
- Analysis and filtering
- Scoring and ranking
- End-to-end pipeline determinism
"""

import unittest
from mnn_pipeline import (
    normalize_query,
    generate_constraints,
    map_constraints_to_indices,
    generate_sequences,
    analyze_sequences,
    score_and_rank,
    output_results,
)
from main import run_pipeline


class TestQueryNormalizer(unittest.TestCase):
    """Test cases for query normalization."""
    
    def test_uppercase_conversion(self):
        """Test that queries are converted to uppercase."""
        result = normalize_query("hello world")
        self.assertEqual(result, "HELLO WORLD")
    
    def test_special_character_removal(self):
        """Test that special characters are removed."""
        result = normalize_query("hello, world!")
        self.assertEqual(result, "HELLO WORLD")
    
    def test_whitespace_normalization(self):
        """Test that extra whitespace is stripped."""
        result = normalize_query("  hello   world  ")
        self.assertEqual(result, "HELLO WORLD")
    
    def test_alphanumeric_preservation(self):
        """Test that alphanumeric characters are preserved."""
        result = normalize_query("AI 2024")
        self.assertEqual(result, "AI 2024")
    
    def test_caching(self):
        """Test that normalization is cached."""
        query = "test query"
        result1 = normalize_query(query)
        result2 = normalize_query(query)
        self.assertEqual(result1, result2)
        self.assertIs(result1, result2)  # Same object (cached)


class TestConstraintGenerator(unittest.TestCase):
    """Test cases for constraint generation."""
    
    def test_constraint_structure(self):
        """Test that constraints have correct structure."""
        constraints = generate_constraints("HELLO")
        self.assertIn('pattern', constraints)
        self.assertIn('min_length', constraints)
        self.assertIn('max_length', constraints)
    
    def test_pattern_matches_input(self):
        """Test that pattern matches the input query."""
        constraints = generate_constraints("ARTIFICIAL INTELLIGENCE")
        self.assertEqual(constraints['pattern'], "ARTIFICIAL INTELLIGENCE")
    
    def test_length_bounds(self):
        """Test that length bounds are calculated correctly."""
        constraints = generate_constraints("HELLO")
        self.assertEqual(constraints['min_length'], 5)
        self.assertEqual(constraints['max_length'], 55)
    
    def test_determinism(self):
        """Test that constraints are deterministic."""
        query = "TEST QUERY"
        result1 = generate_constraints(query)
        result2 = generate_constraints(query)
        self.assertEqual(result1, result2)


class TestIndexMapper(unittest.TestCase):
    """Test cases for index mapping."""
    
    def test_returns_list(self):
        """Test that index mapper returns a list."""
        constraints = {'pattern': 'HELLO', 'min_length': 5, 'max_length': 55}
        indices = map_constraints_to_indices(constraints)
        self.assertIsInstance(indices, list)
    
    def test_generates_1000_indices(self):
        """Test that exactly 1000 indices are generated."""
        constraints = {'pattern': 'HELLO', 'min_length': 5, 'max_length': 55}
        indices = map_constraints_to_indices(constraints)
        self.assertEqual(len(indices), 1000)
    
    def test_step_size_based_on_pattern(self):
        """Test that step size is based on pattern length."""
        constraints = {'pattern': 'HELLO', 'min_length': 5, 'max_length': 55}
        indices = map_constraints_to_indices(constraints)
        # Step should be 5 (length of "HELLO")
        self.assertEqual(indices[1] - indices[0], 5)
    
    def test_determinism(self):
        """Test that index mapping is deterministic."""
        constraints = {'pattern': 'TEST', 'min_length': 4, 'max_length': 54}
        result1 = map_constraints_to_indices(constraints)
        result2 = map_constraints_to_indices(constraints)
        self.assertEqual(result1, result2)


class TestSequenceGenerator(unittest.TestCase):
    """Test cases for sequence generation."""
    
    def test_generates_sequences_for_all_indices(self):
        """Test that a sequence is generated for each index."""
        indices = [0, 5, 10]
        constraints = {'pattern': 'HELLO', 'min_length': 5, 'max_length': 55}
        sequences = generate_sequences(indices, constraints)
        self.assertEqual(len(sequences), len(indices))
    
    def test_sequences_contain_pattern(self):
        """Test that all sequences contain the pattern."""
        indices = [0, 5, 10, 15, 20]
        constraints = {'pattern': 'HELLO', 'min_length': 5, 'max_length': 55}
        sequences = generate_sequences(indices, constraints)
        for sequence in sequences:
            self.assertIn('HELLO', sequence)
    
    def test_book_format(self):
        """Test that sequences use BOOK format."""
        indices = [0]
        constraints = {'pattern': 'HELLO', 'min_length': 5, 'max_length': 55}
        sequences = generate_sequences(indices, constraints)
        self.assertTrue(sequences[0].startswith('BOOK 0:'))
    
    def test_determinism(self):
        """Test that sequence generation is deterministic."""
        indices = [0, 5, 10]
        constraints = {'pattern': 'TEST', 'min_length': 4, 'max_length': 54}
        result1 = generate_sequences(indices, constraints)
        result2 = generate_sequences(indices, constraints)
        self.assertEqual(result1, result2)


class TestAnalyzer(unittest.TestCase):
    """Test cases for sequence analysis."""
    
    def test_filters_by_pattern(self):
        """Test that sequences without pattern are filtered out."""
        sequences = [
            'BOOK 0: HELLO WORLD',
            'BOOK 1: GOODBYE WORLD',
            'BOOK 2: HELLO AGAIN'
        ]
        constraints = {'pattern': 'HELLO', 'min_length': 5, 'max_length': 100}
        valid = analyze_sequences(sequences, constraints)
        self.assertEqual(len(valid), 2)
        for seq in valid:
            self.assertIn('HELLO', seq)
    
    def test_filters_by_length(self):
        """Test that sequences outside length bounds are filtered."""
        sequences = [
            'BOOK 0: HI',  # Too short
            'BOOK 1: HELLO WORLD',  # Good
            'BOOK 2: ' + 'HELLO ' + 'X' * 200  # Too long
        ]
        constraints = {'pattern': 'HELLO', 'min_length': 10, 'max_length': 30}
        valid = analyze_sequences(sequences, constraints)
        self.assertEqual(len(valid), 1)
        self.assertIn('HELLO WORLD', valid[0])
    
    def test_eliminates_duplicates(self):
        """Test that duplicate sequences are eliminated."""
        sequences = [
            'BOOK 0: HELLO WORLD',
            'BOOK 0: HELLO WORLD',  # Exact duplicate
            'BOOK 2: HELLO THERE'
        ]
        constraints = {'pattern': 'HELLO', 'min_length': 5, 'max_length': 100}
        valid = analyze_sequences(sequences, constraints)
        self.assertEqual(len(valid), 2)


class TestScorer(unittest.TestCase):
    """Test cases for scoring and ranking."""
    
    def test_returns_scored_sequences(self):
        """Test that scorer returns sequences with scores."""
        sequences = ['BOOK 0: CONTENT BEFORE HELLO AND CONTENT AFTER']
        constraints = {'pattern': 'HELLO', 'min_length': 5, 'max_length': 100}
        results = score_and_rank(sequences, constraints)
        self.assertEqual(len(results), 1)
        self.assertIn('sequence', results[0])
        self.assertIn('score', results[0])
    
    def test_center_weighted_scoring(self):
        """Test that center-positioned patterns score higher."""
        sequences = [
            'BOOK 0: HELLO AT START',  # Pattern near start
            'BOOK 1: CONTENT HELLO MORE',  # Pattern in middle
            'BOOK 2: LOTS OF CONTENT BEFORE HELLO'  # Pattern near end
        ]
        constraints = {'pattern': 'HELLO', 'min_length': 5, 'max_length': 100}
        results = score_and_rank(sequences, constraints)
        
        # Middle pattern should score highest
        middle_seq = [r for r in results if 'CONTENT HELLO MORE' in r['sequence']][0]
        self.assertGreater(middle_seq['score'], results[-1]['score'])
    
    def test_sorted_descending(self):
        """Test that results are sorted by score descending."""
        sequences = [
            'BOOK 0: HELLO AT START',
            'BOOK 1: MIDDLE HELLO MIDDLE',
            'BOOK 2: START HELLO END'
        ]
        constraints = {'pattern': 'HELLO', 'min_length': 5, 'max_length': 100}
        results = score_and_rank(sequences, constraints)
        
        # Scores should be in descending order
        scores = [r['score'] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))


class TestPipelineDeterminism(unittest.TestCase):
    """Test cases for end-to-end pipeline determinism."""
    
    def test_identical_queries_produce_identical_results(self):
        """Test that the same query produces the same results."""
        query = "artificial intelligence"
        result1 = run_pipeline(query)
        result2 = run_pipeline(query)
        
        # Results should be identical
        self.assertEqual(len(result1), len(result2))
        for r1, r2 in zip(result1, result2):
            self.assertEqual(r1['sequence'], r2['sequence'])
            self.assertEqual(r1['score'], r2['score'])
    
    def test_different_queries_produce_different_results(self):
        """Test that different queries produce different results."""
        result1 = run_pipeline("hello")
        result2 = run_pipeline("goodbye")
        
        # Results should be different
        self.assertNotEqual(result1[0]['sequence'], result2[0]['sequence'])
    
    def test_caching_maintains_determinism(self):
        """Test that caching doesn't affect determinism."""
        query = "neural network"
        
        # First call (cache miss)
        result1 = run_pipeline(query)
        
        # Second call (cache hit)
        result2 = run_pipeline(query)
        
        # Third call (cache hit)
        result3 = run_pipeline(query)
        
        # All should be identical
        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)
    
    def test_returns_top_10_results(self):
        """Test that pipeline returns exactly top 10 results."""
        result = run_pipeline("machine learning")
        self.assertEqual(len(result), 10)
    
    def test_empty_normalized_query_raises_error(self):
        """Test that queries that normalize to empty raise ValueError."""
        with self.assertRaises(ValueError) as context:
            run_pipeline("!!!")
        self.assertIn("normalization", str(context.exception).lower())


class TestOutputHandler(unittest.TestCase):
    """Test cases for output handler."""
    
    def test_output_does_not_crash(self):
        """Test that output handler doesn't crash."""
        sequences = [
            {'sequence': 'BOOK 0: HELLO WORLD', 'score': 0.9},
            {'sequence': 'BOOK 1: WORLD HELLO', 'score': 0.8}
        ]
        try:
            output_results(sequences)
        except Exception as e:
            self.fail(f"output_results raised exception: {e}")


if __name__ == '__main__':
    unittest.main()
