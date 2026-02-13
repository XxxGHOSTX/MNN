"""
Unit tests for Permutation Engine and Conceptual Filter
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import numpy as np
from permutation.engine import PermutationEngine, ConceptualFilter


class TestPermutationEngine(unittest.TestCase):
    """Test cases for Permutation Engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = PermutationEngine(seed=42)
    
    def test_initialization(self):
        """Test engine initialization."""
        self.assertEqual(self.engine.seed, 42)
        self.assertIsNotNone(self.engine.conceptual_filter)
    
    def test_generate_permutation_space(self):
        """Test permutation space generation."""
        dimensions = 5
        cardinality = 29
        result = self.engine.generate_permutation_space(dimensions, cardinality)
        
        self.assertEqual(result.shape, (dimensions, cardinality))
        
        # Check that each row is a valid permutation
        for i in range(dimensions):
            unique_values = len(np.unique(result[i]))
            self.assertEqual(unique_values, cardinality)
    
    def test_mathematical_refinement(self):
        """Test mathematical refinement process."""
        permutation_matrix = np.random.randint(0, 29, size=(5, 29))
        refined = self.engine.mathematical_refinement(permutation_matrix, refinement_iterations=3)
        
        self.assertEqual(refined.shape, permutation_matrix.shape)
        # Check that values are normalized
        self.assertTrue(np.all(refined >= -1))
        self.assertTrue(np.all(refined <= 1))
    
    def test_complete_process(self):
        """Test complete 3-stage process."""
        result = self.engine.process(
            dimensions=5,
            cardinality=29,
            refinement_iterations=3
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.shape, (5, 29))
    
    def test_reproducibility(self):
        """Test that same seed produces same results."""
        engine1 = PermutationEngine(seed=42)
        engine2 = PermutationEngine(seed=42)
        
        result1 = engine1.generate_permutation_space(5, 29)
        result2 = engine2.generate_permutation_space(5, 29)
        
        np.testing.assert_array_equal(result1, result2)


class TestConceptualFilter(unittest.TestCase):
    """Test cases for Conceptual Filter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.filter = ConceptualFilter()
    
    def test_initialization(self):
        """Test filter initialization."""
        self.assertEqual(self.filter.threshold, 0.5)
    
    def test_filter_peaks(self):
        """Test peak pattern extraction."""
        matrix = np.array([[-1, 0.3, 0.7, 0.9, 0.2]])
        result = self.filter.filter(matrix, threshold=0.5, pattern_type="peaks")
        
        # Should keep values > 0.5
        self.assertEqual(result[0, 0], 0)
        self.assertEqual(result[0, 1], 0)
        self.assertGreater(result[0, 2], 0)
        self.assertGreater(result[0, 3], 0)
    
    def test_filter_valleys(self):
        """Test valley pattern extraction."""
        matrix = np.array([[-1, -0.3, 0.7, 0.9, -0.8]])
        result = self.filter.filter(matrix, threshold=0.5, pattern_type="valleys")
        
        # Should keep values < -0.5
        self.assertLess(result[0, 0], 0)
        self.assertLess(result[0, 4], 0)
        self.assertEqual(result[0, 2], 0)
    
    def test_filter_edges(self):
        """Test edge pattern extraction."""
        # Use 2D matrix with sufficient size for gradient calculation
        matrix = np.array([[0, 0, 1, 1, 0, 0],
                          [0, 0, 1, 1, 0, 0]])
        result = self.filter.filter(matrix, threshold=0.3, pattern_type="edges")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.shape, matrix.shape)


if __name__ == '__main__':
    unittest.main()
