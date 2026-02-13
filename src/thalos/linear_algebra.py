"""
THALOS Linear Algebra Stack
Custom matrix operations for neural network computations.
"""

import numpy as np
from typing import Union, List


class ThalosMatrix:
    """
    Custom matrix implementation for THALOS linear algebra stack.
    Provides optimized operations for neural network computations.
    """
    
    def __init__(self, data: Union[np.ndarray, List, float]):
        """
        Initialize a THALOS matrix.
        
        Args:
            data: Input data (numpy array, list, or scalar)
        """
        if isinstance(data, (int, float)):
            self.data = np.array([[data]])
        elif isinstance(data, list):
            self.data = np.array(data)
        elif isinstance(data, np.ndarray):
            self.data = data.copy()
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")
    
    @property
    def shape(self):
        """Return the shape of the matrix."""
        return self.data.shape
    
    def __repr__(self):
        return f"ThalosMatrix(shape={self.shape})\n{self.data}"
    
    def __add__(self, other):
        """Matrix addition."""
        if isinstance(other, ThalosMatrix):
            return ThalosMatrix(self.data + other.data)
        return ThalosMatrix(self.data + other)
    
    def __mul__(self, other):
        """Element-wise multiplication."""
        if isinstance(other, ThalosMatrix):
            return ThalosMatrix(self.data * other.data)
        return ThalosMatrix(self.data * other)
    
    def matmul(self, other):
        """Matrix multiplication."""
        if isinstance(other, ThalosMatrix):
            return ThalosMatrix(np.matmul(self.data, other.data))
        return ThalosMatrix(np.matmul(self.data, other))
    
    def transpose(self):
        """Transpose the matrix."""
        return ThalosMatrix(self.data.T)
    
    def apply_activation(self, activation: str = "relu"):
        """
        Apply activation function.
        
        Args:
            activation: Activation function name ('relu', 'sigmoid', 'tanh')
        """
        if activation == "relu":
            return ThalosMatrix(np.maximum(0, self.data))
        elif activation == "sigmoid":
            return ThalosMatrix(1 / (1 + np.exp(-self.data)))
        elif activation == "tanh":
            return ThalosMatrix(np.tanh(self.data))
        else:
            raise ValueError(f"Unsupported activation: {activation}")
    
    def flatten(self):
        """Flatten the matrix to 1D."""
        return ThalosMatrix(self.data.flatten())
    
    def reshape(self, *shape):
        """Reshape the matrix."""
        return ThalosMatrix(self.data.reshape(shape))
