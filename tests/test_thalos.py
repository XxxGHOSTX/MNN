"""
Unit tests for THALOS Linear Algebra Stack
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import numpy as np
from thalos.linear_algebra import ThalosMatrix


class TestThalosMatrix(unittest.TestCase):
    """Test cases for ThalosMatrix custom linear algebra."""
    
    def test_initialization_from_array(self):
        """Test matrix initialization from numpy array."""
        data = np.array([[1, 2], [3, 4]])
        matrix = ThalosMatrix(data)
        self.assertEqual(matrix.shape, (2, 2))
        np.testing.assert_array_equal(matrix.data, data)
    
    def test_initialization_from_list(self):
        """Test matrix initialization from list."""
        data = [[1, 2], [3, 4]]
        matrix = ThalosMatrix(data)
        self.assertEqual(matrix.shape, (2, 2))
    
    def test_initialization_from_scalar(self):
        """Test matrix initialization from scalar."""
        matrix = ThalosMatrix(5.0)
        self.assertEqual(matrix.shape, (1, 1))
        self.assertEqual(matrix.data[0, 0], 5.0)
    
    def test_addition(self):
        """Test matrix addition."""
        m1 = ThalosMatrix([[1, 2], [3, 4]])
        m2 = ThalosMatrix([[5, 6], [7, 8]])
        result = m1 + m2
        expected = np.array([[6, 8], [10, 12]])
        np.testing.assert_array_equal(result.data, expected)
    
    def test_multiplication(self):
        """Test element-wise multiplication."""
        m1 = ThalosMatrix([[1, 2], [3, 4]])
        m2 = ThalosMatrix([[2, 2], [2, 2]])
        result = m1 * m2
        expected = np.array([[2, 4], [6, 8]])
        np.testing.assert_array_equal(result.data, expected)
    
    def test_matmul(self):
        """Test matrix multiplication."""
        m1 = ThalosMatrix([[1, 2], [3, 4]])
        m2 = ThalosMatrix([[5, 6], [7, 8]])
        result = m1.matmul(m2)
        expected = np.array([[19, 22], [43, 50]])
        np.testing.assert_array_equal(result.data, expected)
    
    def test_transpose(self):
        """Test matrix transpose."""
        matrix = ThalosMatrix([[1, 2, 3], [4, 5, 6]])
        result = matrix.transpose()
        expected = np.array([[1, 4], [2, 5], [3, 6]])
        np.testing.assert_array_equal(result.data, expected)
    
    def test_relu_activation(self):
        """Test ReLU activation function."""
        matrix = ThalosMatrix([[-1, 0, 1], [2, -3, 4]])
        result = matrix.apply_activation("relu")
        expected = np.array([[0, 0, 1], [2, 0, 4]])
        np.testing.assert_array_equal(result.data, expected)
    
    def test_sigmoid_activation(self):
        """Test sigmoid activation function."""
        matrix = ThalosMatrix([[0]])
        result = matrix.apply_activation("sigmoid")
        self.assertAlmostEqual(result.data[0, 0], 0.5, places=5)
    
    def test_tanh_activation(self):
        """Test tanh activation function."""
        matrix = ThalosMatrix([[0]])
        result = matrix.apply_activation("tanh")
        self.assertAlmostEqual(result.data[0, 0], 0.0, places=5)
    
    def test_flatten(self):
        """Test matrix flattening."""
        matrix = ThalosMatrix([[1, 2], [3, 4]])
        result = matrix.flatten()
        expected = np.array([1, 2, 3, 4])
        np.testing.assert_array_equal(result.data, expected)
    
    def test_reshape(self):
        """Test matrix reshaping."""
        matrix = ThalosMatrix([[1, 2, 3, 4]])
        result = matrix.reshape(2, 2)
        self.assertEqual(result.shape, (2, 2))


if __name__ == '__main__':
    unittest.main()
