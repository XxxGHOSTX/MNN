"""
Weight Encryption System
Encrypts neural network parameters using hardware-derived rotating keys.
"""

import hashlib
import uuid
import platform
import os
from typing import Optional, Dict
import numpy as np


class HardwareIDGenerator:
    """
    Generate unique hardware ID for encryption key derivation.
    """
    
    @staticmethod
    def get_hardware_id() -> str:
        """
        Generate a unique hardware ID based on system characteristics.
        
        Returns:
            Hardware ID string
        """
        # Collect system information
        components = [
            platform.machine(),
            platform.processor(),
            platform.system(),
            str(uuid.getnode()),  # MAC address
        ]
        
        # Create deterministic hash
        hw_string = "|".join(components)
        hardware_id = hashlib.sha256(hw_string.encode()).hexdigest()
        
        return hardware_id
    
    @staticmethod
    def derive_key(hardware_id: str, rotation_index: int = 0) -> bytes:
        """
        Derive encryption key from hardware ID with rotation support.
        
        Args:
            hardware_id: Base hardware identifier
            rotation_index: Key rotation index for time-based rotation
            
        Returns:
            32-byte encryption key
        """
        # Combine hardware ID with rotation index
        key_material = f"{hardware_id}:{rotation_index}".encode()
        
        # Generate key using SHA-256
        key = hashlib.sha256(key_material).digest()
        
        return key


class WeightEncryptor:
    """
    Encrypt and decrypt neural network weights using hardware-derived keys.
    Ensures binary-level protection of the "intelligence" during training.
    """
    
    def __init__(self, hardware_id: Optional[str] = None):
        """
        Initialize the weight encryptor.
        
        Args:
            hardware_id: Hardware ID for key derivation (auto-detected if None)
        """
        if hardware_id is None:
            self.hardware_id = HardwareIDGenerator.get_hardware_id()
        else:
            self.hardware_id = hardware_id
        
        self.rotation_index = 0
        self.current_key = self._generate_key()
    
    def _generate_key(self) -> bytes:
        """Generate encryption key for current rotation index."""
        return HardwareIDGenerator.derive_key(self.hardware_id, self.rotation_index)
    
    def rotate_key(self):
        """
        Rotate to the next encryption key.
        Should be called periodically during training.
        """
        self.rotation_index += 1
        self.current_key = self._generate_key()
    
    def encrypt_weights(self, weights: np.ndarray) -> Dict[str, any]:
        """
        Encrypt neural network weights.
        
        Args:
            weights: Weight matrix to encrypt
            
        Returns:
            Dictionary containing encrypted data and metadata
        """
        # Convert weights to bytes
        weights_bytes = weights.tobytes()
        
        # Generate encryption key stream
        key_stream = self._generate_key_stream(len(weights_bytes))
        
        # XOR encryption (simple but effective for binary protection)
        encrypted_bytes = bytes(a ^ b for a, b in zip(weights_bytes, key_stream))
        
        # Store metadata for decryption
        encrypted_data = {
            "encrypted_weights": encrypted_bytes,
            "shape": weights.shape,
            "dtype": str(weights.dtype),
            "rotation_index": self.rotation_index,
            "hardware_id_hash": hashlib.sha256(self.hardware_id.encode()).hexdigest()[:16]
        }
        
        return encrypted_data
    
    def decrypt_weights(self, encrypted_data: Dict[str, any]) -> np.ndarray:
        """
        Decrypt neural network weights.
        
        Args:
            encrypted_data: Dictionary containing encrypted data and metadata
            
        Returns:
            Decrypted weight matrix
        """
        # Verify hardware ID (partial check for security)
        expected_hash = hashlib.sha256(self.hardware_id.encode()).hexdigest()[:16]
        if encrypted_data["hardware_id_hash"] != expected_hash:
            raise ValueError("Hardware ID mismatch - weights encrypted on different system")
        
        # Set rotation index to match encryption
        original_rotation = self.rotation_index
        self.rotation_index = encrypted_data["rotation_index"]
        key = self._generate_key()
        
        # Decrypt
        encrypted_bytes = encrypted_data["encrypted_weights"]
        key_stream = self._generate_key_stream(len(encrypted_bytes))
        decrypted_bytes = bytes(a ^ b for a, b in zip(encrypted_bytes, key_stream))
        
        # Restore rotation index
        self.rotation_index = original_rotation
        self.current_key = self._generate_key()
        
        # Convert back to numpy array
        dtype = np.dtype(encrypted_data["dtype"])
        weights = np.frombuffer(decrypted_bytes, dtype=dtype)
        weights = weights.reshape(encrypted_data["shape"])
        
        return weights
    
    def _generate_key_stream(self, length: int) -> bytes:
        """
        Generate a key stream for encryption/decryption.
        
        Args:
            length: Required length of key stream
            
        Returns:
            Key stream bytes
        """
        key_stream = bytearray()
        counter = 0
        
        while len(key_stream) < length:
            # Generate block using key and counter
            block_material = self.current_key + counter.to_bytes(8, 'big')
            block = hashlib.sha256(block_material).digest()
            key_stream.extend(block)
            counter += 1
        
        return bytes(key_stream[:length])
    
    def get_encryption_info(self) -> Dict[str, any]:
        """
        Get current encryption state information.
        
        Returns:
            Dictionary with encryption info
        """
        return {
            "hardware_id_hash": hashlib.sha256(self.hardware_id.encode()).hexdigest()[:16],
            "rotation_index": self.rotation_index,
            "key_available": self.current_key is not None
        }
