"""
Permutation Engine - Inspired by https://libraryofbabel.info
Implements 3-stage mathematical refinement process with Conceptual Filter.
"""

import hashlib
import itertools
from typing import List, Any, Dict
import numpy as np


class PermutationEngine:
    """
    Permutation Engine that replicates the logic of https://libraryofbabel.info.
    Implements a 3-stage mathematical refinement process:
    1. Initial Permutation Generation
    2. Mathematical Refinement
    3. Conceptual Filtering
    """
    
    def __init__(self, seed: int = 42):
        """
        Initialize the Permutation Engine.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        self.rng = np.random.RandomState(seed)
        self.conceptual_filter = ConceptualFilter()
    
    def generate_permutation_space(self, dimensions: int, cardinality: int = 256):
        """
        Stage 1: Generate initial permutation space.
        
        Args:
            dimensions: Number of dimensions in the permutation space
            cardinality: Size of the alphabet/symbol set
            
        Returns:
            Initial permutation matrix
        """
        # Generate a permutation vector that maps each index to a unique position
        permutation = self.rng.permutation(cardinality)
        
        # Extend to multiple dimensions
        permutation_matrix = np.zeros((dimensions, cardinality), dtype=np.int32)
        for i in range(dimensions):
            # Create unique permutation for each dimension using seed + dimension
            temp_rng = np.random.RandomState(self.seed + i)
            permutation_matrix[i] = temp_rng.permutation(cardinality)
        
        return permutation_matrix
    
    def mathematical_refinement(self, permutation_matrix: np.ndarray, 
                                refinement_iterations: int = 3):
        """
        Stage 2: Apply mathematical refinement to the permutation matrix.
        Uses iterative transformations to refine the permutation space.
        
        Args:
            permutation_matrix: Initial permutation matrix
            refinement_iterations: Number of refinement iterations
            
        Returns:
            Refined permutation matrix
        """
        refined = permutation_matrix.copy().astype(np.float64)
        
        for iteration in range(refinement_iterations):
            # Apply rotation transformation
            rotation_angle = np.pi / (2 * (iteration + 1))
            rotation_matrix = self._create_rotation_matrix(
                refined.shape[0], rotation_angle
            )
            refined = rotation_matrix @ refined
            
            # Apply normalization
            refined = (refined - refined.min()) / (refined.max() - refined.min() + 1e-8)
            
            # Apply non-linear transformation
            refined = np.tanh(refined * 2 - 1)
        
        return refined
    
    def _create_rotation_matrix(self, size: int, angle: float):
        """
        Create a rotation matrix for the mathematical refinement.
        
        Args:
            size: Size of the square rotation matrix
            angle: Rotation angle in radians
            
        Returns:
            Rotation matrix
        """
        # For higher dimensions, create a block-diagonal rotation matrix
        rotation = np.eye(size)
        for i in range(0, size - 1, 2):
            rotation[i:i+2, i:i+2] = [
                [np.cos(angle), -np.sin(angle)],
                [np.sin(angle), np.cos(angle)]
            ]
        return rotation
    
    def apply_conceptual_filter(self, refined_matrix: np.ndarray, 
                                filter_params: Dict[str, Any] = None):
        """
        Stage 3: Apply conceptual filter to extract meaningful patterns.
        
        Args:
            refined_matrix: Refined permutation matrix
            filter_params: Parameters for the conceptual filter
            
        Returns:
            Filtered output
        """
        if filter_params is None:
            filter_params = {}
        
        return self.conceptual_filter.filter(refined_matrix, **filter_params)
    
    def process(self, dimensions: int, cardinality: int = 256, 
                refinement_iterations: int = 3, filter_params: Dict[str, Any] = None):
        """
        Complete 3-stage process: Generation -> Refinement -> Filtering
        
        Args:
            dimensions: Permutation space dimensions
            cardinality: Symbol set size
            refinement_iterations: Number of refinement passes
            filter_params: Conceptual filter parameters
            
        Returns:
            Final processed output
        """
        # Stage 1: Generate permutation space
        permutation_matrix = self.generate_permutation_space(dimensions, cardinality)
        
        # Stage 2: Apply mathematical refinement
        refined_matrix = self.mathematical_refinement(
            permutation_matrix, refinement_iterations
        )
        
        # Stage 3: Apply conceptual filter
        filtered_output = self.apply_conceptual_filter(refined_matrix, filter_params)
        
        return filtered_output


class ConceptualFilter:
    """
    Conceptual Filter for extracting meaningful patterns from permutation space.
    """
    
    def __init__(self):
        """Initialize the conceptual filter."""
        self.threshold = 0.5
    
    def filter(self, matrix: np.ndarray, threshold: float = None, 
               pattern_type: str = "peaks") -> np.ndarray:
        """
        Apply conceptual filtering to extract patterns.
        
        Args:
            matrix: Input matrix to filter
            threshold: Filtering threshold (0.0 to 1.0)
            pattern_type: Type of pattern to extract ('peaks', 'valleys', 'edges')
            
        Returns:
            Filtered matrix
        """
        if threshold is None:
            threshold = self.threshold
        
        if pattern_type == "peaks":
            # Extract high-value peaks
            return self._extract_peaks(matrix, threshold)
        elif pattern_type == "valleys":
            # Extract low-value valleys
            return self._extract_valleys(matrix, threshold)
        elif pattern_type == "edges":
            # Extract edge patterns
            return self._extract_edges(matrix, threshold)
        else:
            # Default: threshold-based filtering
            return np.where(np.abs(matrix) > threshold, matrix, 0)
    
    def _extract_peaks(self, matrix: np.ndarray, threshold: float) -> np.ndarray:
        """Extract peak patterns (local maxima)."""
        peaks = np.zeros_like(matrix)
        peaks[matrix > threshold] = matrix[matrix > threshold]
        return peaks
    
    def _extract_valleys(self, matrix: np.ndarray, threshold: float) -> np.ndarray:
        """Extract valley patterns (local minima)."""
        valleys = np.zeros_like(matrix)
        valleys[matrix < -threshold] = matrix[matrix < -threshold]
        return valleys
    
    def _extract_edges(self, matrix: np.ndarray, threshold: float) -> np.ndarray:
        """Extract edge patterns using gradient."""
        # Compute gradients
        if matrix.ndim == 1:
            gradient = np.gradient(matrix)
            edges = np.where(np.abs(gradient) > threshold, matrix, 0)
        else:
            gradient_y = np.gradient(matrix, axis=0)
            gradient_x = np.gradient(matrix, axis=1)
            gradient_magnitude = np.sqrt(gradient_y**2 + gradient_x**2)
            edges = np.where(gradient_magnitude > threshold, matrix, 0)
        return edges
