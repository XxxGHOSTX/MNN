"""
Matrix Neural Network (MNN)
A neural network library with encrypted weights and custom linear algebra.
"""

__version__ = "0.1.0"

from .thalos.linear_algebra import ThalosMatrix
from .permutation.engine import PermutationEngine
from .encryption.weight_encryptor import WeightEncryptor
from .mind.llm_handler import MindLLMHandler
from .buffer.relational_buffer import RelationalBuffer

__all__ = [
    "ThalosMatrix",
    "PermutationEngine",
    "WeightEncryptor",
    "MindLLMHandler",
    "RelationalBuffer",
]
