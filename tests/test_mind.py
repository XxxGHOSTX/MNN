"""
Unit tests for Mind (LLM) Handler
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import numpy as np
from mind.llm_handler import MindLLMHandler, GeometricCharacterEmbedding, SemanticSieve


class TestGeometricCharacterEmbedding(unittest.TestCase):
    """Test cases for Geometric Character Embeddings."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.embedding = GeometricCharacterEmbedding(embedding_dim=128)
    
    def test_initialization(self):
        """Test embedding initialization."""
        self.assertEqual(self.embedding.embedding_dim, 128)
        self.assertEqual(self.embedding.num_chars, 29)
        self.assertEqual(len(self.embedding.CHARACTER_SET), 29)
    
    def test_character_set(self):
        """Test that character set contains expected characters."""
        char_set = self.embedding.CHARACTER_SET
        
        # Check lowercase letters
        for char in 'abcdefghijklmnopqrstuvwxyz':
            self.assertIn(char, char_set)
        
        # Check special characters
        self.assertIn(' ', char_set)
        self.assertIn(',', char_set)
        self.assertIn('.', char_set)
    
    def test_encode(self):
        """Test text encoding."""
        text = "hello world"
        embeddings = self.embedding.encode(text)
        
        self.assertEqual(embeddings.shape, (len(text), self.embedding.embedding_dim))
    
    def test_decode(self):
        """Test embedding decoding."""
        text = "test"
        embeddings = self.embedding.encode(text)
        decoded = self.embedding.decode(embeddings)
        
        self.assertEqual(decoded, text)
    
    def test_relational_distance(self):
        """Test relational distance calculation."""
        dist_aa = self.embedding.relational_distance('a', 'a')
        dist_ab = self.embedding.relational_distance('a', 'b')
        
        # Distance to self should be 0
        self.assertAlmostEqual(dist_aa, 0.0, places=5)
        
        # Distance to different character should be > 0
        self.assertGreater(dist_ab, 0.0)


class TestSemanticSieve(unittest.TestCase):
    """Test cases for Semantic Sieve."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sieve = SemanticSieve(noise_threshold=0.99999)
    
    def test_initialization(self):
        """Test sieve initialization."""
        self.assertEqual(self.sieve.noise_threshold, 0.99999)
        self.assertIsNotNone(self.sieve.valid_bigrams)
    
    def test_filter_valid_text(self):
        """Test filtering of linguistically valid text."""
        # Text with common bigrams
        text = "the quick brown"
        is_valid, confidence = self.sieve.filter(text)
        
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_filter_random_text(self):
        """Test filtering of random noise."""
        # Random characters (likely low confidence)
        text = "xqzjkw"
        is_valid, confidence = self.sieve.filter(text)
        
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(confidence, float)
    
    def test_filter_empty_text(self):
        """Test filtering of empty/short text."""
        is_valid, confidence = self.sieve.filter("a")
        
        self.assertFalse(is_valid)
        self.assertEqual(confidence, 0.0)


class TestMindLLMHandler(unittest.TestCase):
    """Test cases for Mind LLM Handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mind = MindLLMHandler(embedding_dim=128, hidden_dim=256)
    
    def test_initialization(self):
        """Test Mind handler initialization."""
        self.assertEqual(self.mind.embedding_dim, 128)
        self.assertEqual(self.mind.hidden_dim, 256)
        self.assertIsNotNone(self.mind.character_embedding)
        self.assertIsNotNone(self.mind.semantic_sieve)
        self.assertIsNotNone(self.mind.parameters)
    
    def test_parameters_initialization(self):
        """Test that MNN parameters are initialized."""
        params = self.mind.parameters
        
        self.assertIn("embedding_projection", params)
        self.assertIn("hidden_layer_1", params)
        self.assertIn("hidden_layer_2", params)
        self.assertIn("output_projection", params)
        
        # Check shapes
        self.assertEqual(
            params["embedding_projection"].shape,
            (self.mind.embedding_dim, self.mind.hidden_dim)
        )
    
    def test_generate(self):
        """Test text generation."""
        prompt = "hello"
        generated = self.mind.generate(prompt, max_length=10, temperature=0.5)
        
        self.assertIsInstance(generated, str)
        self.assertTrue(generated.startswith(prompt))
    
    def test_evaluate_confidence(self):
        """Test confidence evaluation."""
        text = "the"
        confidence = self.mind.evaluate_confidence(text)
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)


if __name__ == '__main__':
    unittest.main()
