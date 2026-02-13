"""
Unit tests for Weight Encryption System
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import numpy as np
from encryption.weight_encryptor import WeightEncryptor, HardwareIDGenerator


class TestHardwareIDGenerator(unittest.TestCase):
    """Test cases for Hardware ID generation."""
    
    def test_hardware_id_generation(self):
        """Test that hardware ID is generated."""
        hw_id = HardwareIDGenerator.get_hardware_id()
        self.assertIsNotNone(hw_id)
        self.assertGreater(len(hw_id), 0)
    
    def test_hardware_id_consistency(self):
        """Test that hardware ID is consistent across calls."""
        hw_id1 = HardwareIDGenerator.get_hardware_id()
        hw_id2 = HardwareIDGenerator.get_hardware_id()
        self.assertEqual(hw_id1, hw_id2)
    
    def test_key_derivation(self):
        """Test encryption key derivation."""
        hw_id = "test_hardware_id"
        key = HardwareIDGenerator.derive_key(hw_id, rotation_index=0)
        
        self.assertEqual(len(key), 32)  # SHA-256 produces 32 bytes
    
    def test_key_rotation(self):
        """Test that different rotation indices produce different keys."""
        hw_id = "test_hardware_id"
        key1 = HardwareIDGenerator.derive_key(hw_id, rotation_index=0)
        key2 = HardwareIDGenerator.derive_key(hw_id, rotation_index=1)
        
        self.assertNotEqual(key1, key2)


class TestWeightEncryptor(unittest.TestCase):
    """Test cases for Weight Encryption."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.encryptor = WeightEncryptor(hardware_id="test_hardware_id")
    
    def test_initialization(self):
        """Test encryptor initialization."""
        self.assertEqual(self.encryptor.hardware_id, "test_hardware_id")
        self.assertEqual(self.encryptor.rotation_index, 0)
        self.assertIsNotNone(self.encryptor.current_key)
    
    def test_encrypt_decrypt_weights(self):
        """Test weight encryption and decryption."""
        # Create sample weights
        weights = np.random.randn(10, 10)
        
        # Encrypt
        encrypted_data = self.encryptor.encrypt_weights(weights)
        
        # Verify encrypted data structure
        self.assertIn("encrypted_weights", encrypted_data)
        self.assertIn("shape", encrypted_data)
        self.assertIn("dtype", encrypted_data)
        self.assertIn("rotation_index", encrypted_data)
        
        # Decrypt
        decrypted_weights = self.encryptor.decrypt_weights(encrypted_data)
        
        # Verify decryption correctness
        np.testing.assert_array_almost_equal(weights, decrypted_weights)
    
    def test_key_rotation(self):
        """Test encryption key rotation."""
        initial_index = self.encryptor.rotation_index
        initial_key = self.encryptor.current_key
        
        self.encryptor.rotate_key()
        
        self.assertEqual(self.encryptor.rotation_index, initial_index + 1)
        self.assertNotEqual(self.encryptor.current_key, initial_key)
    
    def test_encryption_with_different_keys(self):
        """Test that different keys produce different encrypted data."""
        weights = np.random.randn(5, 5)
        
        # Encrypt with first key
        encrypted1 = self.encryptor.encrypt_weights(weights)
        
        # Rotate key
        self.encryptor.rotate_key()
        
        # Encrypt same weights with second key
        encrypted2 = self.encryptor.encrypt_weights(weights)
        
        # Encrypted data should be different
        self.assertNotEqual(
            encrypted1["encrypted_weights"],
            encrypted2["encrypted_weights"]
        )
    
    def test_hardware_id_mismatch(self):
        """Test that decryption fails with wrong hardware ID."""
        weights = np.random.randn(5, 5)
        encrypted_data = self.encryptor.encrypt_weights(weights)
        
        # Create new encryptor with different hardware ID
        other_encryptor = WeightEncryptor(hardware_id="different_hardware_id")
        
        # Decryption should fail
        with self.assertRaises(ValueError):
            other_encryptor.decrypt_weights(encrypted_data)
    
    def test_get_encryption_info(self):
        """Test encryption info retrieval."""
        info = self.encryptor.get_encryption_info()
        
        self.assertIn("hardware_id_hash", info)
        self.assertIn("rotation_index", info)
        self.assertIn("key_available", info)
        self.assertTrue(info["key_available"])


if __name__ == '__main__':
    unittest.main()
