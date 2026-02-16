"""
Unit tests for ThalosBridge middleware and weight encryption from PR #3.
Tests the database operations and hardware-bound weight encryption.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path

# Set environment variables BEFORE importing modules that read them at module level
os.environ["THALOS_DB_DSN"] = os.environ.get("THALOS_DB_DSN", "postgresql://test:test@localhost:5432/test")
os.environ["THALOS_DB_CONNECT_TIMEOUT"] = os.environ.get("THALOS_DB_CONNECT_TIMEOUT", "10")

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from middleware import ThalosBridge, SEVERITY_LEVELS
from weight_encryptor import WeightEncryptor, EncryptedWeights


class TestWeightEncryptor(unittest.TestCase):
    """Test cases for hardware-bound weight encryption."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a fixed hardware ID for testing
        os.environ["THALOS_HARDWARE_ID"] = "test-hardware-12345"
        self.encryptor = WeightEncryptor(iterations=1000)  # Use fewer iterations for faster tests

    def tearDown(self):
        """Clean up after tests."""
        if "THALOS_HARDWARE_ID" in os.environ:
            del os.environ["THALOS_HARDWARE_ID"]

    def test_hardware_fingerprint(self):
        """Test that hardware fingerprint is retrieved correctly."""
        fingerprint = self.encryptor.hardware_fingerprint()
        self.assertEqual(fingerprint, "test-hardware-12345")

    def test_hardware_fingerprint_fallback(self):
        """Test hardware fingerprint generation when env var not set."""
        del os.environ["THALOS_HARDWARE_ID"]
        encryptor = WeightEncryptor()
        fingerprint = encryptor.hardware_fingerprint()
        # Should contain hostname and MAC address
        self.assertIsNotNone(fingerprint)
        self.assertGreater(len(fingerprint), 0)
        self.assertIn("-", fingerprint)

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly."""
        original_data = b"test neural network weights data"

        # Encrypt
        encrypted = self.encryptor.encrypt(original_data)

        # Verify encrypted structure
        self.assertIsInstance(encrypted, EncryptedWeights)
        self.assertIsInstance(encrypted.ciphertext, bytes)
        self.assertIsInstance(encrypted.nonce, bytes)
        self.assertIsInstance(encrypted.salt, bytes)
        self.assertEqual(encrypted.hardware_fingerprint, "test-hardware-12345")
        self.assertEqual(len(encrypted.nonce), 12)  # AES-GCM nonce size
        self.assertEqual(len(encrypted.salt), 16)   # Salt size

        # Decrypt
        decrypted = self.encryptor.decrypt(encrypted)

        # Verify data integrity
        self.assertEqual(original_data, decrypted)

    def test_encrypt_with_associated_data(self):
        """Test encryption with additional authenticated data."""
        weights = b"model weights"
        aad = b"model-name-v1"

        encrypted = self.encryptor.encrypt(weights, associated_data=aad)
        decrypted = self.encryptor.decrypt(encrypted, associated_data=aad)

        self.assertEqual(weights, decrypted)

    def test_decrypt_wrong_associated_data_fails(self):
        """Test that decryption fails with wrong associated data."""
        weights = b"model weights"
        encrypted = self.encryptor.encrypt(weights, associated_data=b"correct-aad")

        # Should fail with wrong AAD
        with self.assertRaises(Exception):  # cryptography raises InvalidTag
            self.encryptor.decrypt(encrypted, associated_data=b"wrong-aad")

    def test_hardware_fingerprint_mismatch(self):
        """Test that decryption fails with wrong hardware fingerprint."""
        weights = b"test data"
        encrypted = self.encryptor.encrypt(weights)

        # Change hardware ID
        os.environ["THALOS_HARDWARE_ID"] = "different-hardware-67890"
        different_encryptor = WeightEncryptor()

        # Should fail with fingerprint mismatch
        with self.assertRaises(ValueError) as cm:
            different_encryptor.decrypt(encrypted)

        self.assertIn("Hardware fingerprint mismatch", str(cm.exception))

    def test_checksum_verification(self):
        """Test that checksum is validated during decryption."""
        weights = b"test data"
        encrypted = self.encryptor.encrypt(weights)

        # Tamper with checksum
        tampered = EncryptedWeights(
            ciphertext=encrypted.ciphertext,
            nonce=encrypted.nonce,
            salt=encrypted.salt,
            hardware_fingerprint=encrypted.hardware_fingerprint,
            checksum="wrong_checksum"
        )

        # Should fail checksum verification
        with self.assertRaises(ValueError) as cm:
            self.encryptor.decrypt(tampered)

        self.assertIn("Checksum verification failed", str(cm.exception))

    def test_custom_salt(self):
        """Test encryption with custom salt."""
        weights = b"test data"
        custom_salt = b"1234567890123456"  # 16 bytes

        encrypted = self.encryptor.encrypt(weights, salt=custom_salt)
        self.assertEqual(encrypted.salt, custom_salt)

        # Should still decrypt correctly
        decrypted = self.encryptor.decrypt(encrypted)
        self.assertEqual(weights, decrypted)

    def test_checksum_function(self):
        """Test that checksum function produces correct hash."""
        data = b"test data"
        checksum = WeightEncryptor.checksum(data)

        # Should be a SHA-256 hex digest (64 characters)
        self.assertEqual(len(checksum), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in checksum))


class TestThalosBridge(unittest.TestCase):
    """Test cases for ThalosBridge middleware (mocked database)."""

    @classmethod
    def setUpClass(cls):
        """Set up class-level environment for all tests."""
        os.environ["THALOS_DB_DSN"] = "postgresql://test:test@localhost:5432/test"
        os.environ["THALOS_HARDWARE_ID"] = "test-hardware-12345"

    def setUp(self):
        """Set up test fixtures with mocked database."""
        # Ensure env vars are set for each test
        os.environ["THALOS_DB_DSN"] = "postgresql://test:test@localhost:5432/test"
        os.environ["THALOS_HARDWARE_ID"] = "test-hardware-12345"

    def test_initialization_with_dsn_arg(self):
        """Test bridge initialization with DSN argument."""
        bridge = ThalosBridge(dsn="postgresql://user:pass@host:5432/db")
        self.assertEqual(bridge.dsn, "postgresql://user:pass@host:5432/db")

    def test_initialization_with_env_var(self):
        """Test bridge initialization with environment variable."""
        bridge = ThalosBridge()
        self.assertEqual(bridge.dsn, "postgresql://test:test@localhost:5432/test")

    def test_initialization_no_dsn_fails(self):
        """Test that initialization fails without DSN."""
        # Pass empty DSN to override the env var
        # After strip(), it should be empty and raise ValueError
        try:
            bridge = ThalosBridge(dsn="   ")  # Only whitespace, should become empty after strip
            self.fail("Expected ValueError to be raised")
        except ValueError as e:
            self.assertIn("Database DSN must be provided", str(e))

    def test_initialization_control_characters_fail(self):
        """Test that DSN with control characters is rejected."""
        with self.assertRaises(ValueError) as cm:
            ThalosBridge(dsn="postgresql://test\ninjection@host/db")
        self.assertIn("control characters", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            ThalosBridge(dsn="postgresql://test\rinjection@host/db")
        self.assertIn("control characters", str(cm.exception))

    def test_dsn_whitespace_stripped(self):
        """Test that DSN whitespace is stripped."""
        bridge = ThalosBridge(dsn="  postgresql://host/db  ")
        self.assertEqual(bridge.dsn, "postgresql://host/db")

    def test_resolve_aad_default(self):
        """Test associated data resolution with default."""
        aad = ThalosBridge._resolve_aad("model-name", None)
        self.assertEqual(aad, b"model-name")

    def test_resolve_aad_explicit(self):
        """Test associated data resolution with explicit value."""
        aad = ThalosBridge._resolve_aad("model-name", b"custom-aad")
        self.assertEqual(aad, b"custom-aad")

    def test_severity_validation(self):
        """Test that severity levels are properly validated."""
        # Valid severities
        valid_severities = ["debug", "info", "warn", "error", "fatal"]
        for severity in valid_severities:
            self.assertIn(severity, SEVERITY_LEVELS)

        # Check ordering
        self.assertEqual(SEVERITY_LEVELS, ("debug", "info", "warn", "error", "fatal"))


class TestThalosBridgeIntegration(unittest.TestCase):
    """Integration tests for ThalosBridge with real database (requires PostgreSQL)."""

    @classmethod
    def setUpClass(cls):
        """Check if we can run integration tests."""
        cls.can_run = False
        dsn = os.getenv("THALOS_DB_DSN")
        if dsn and "test" in dsn.lower():
            cls.can_run = True

    def setUp(self):
        """Set up for integration tests."""
        if not self.can_run:
            self.skipTest("THALOS_DB_DSN not set or not a test database")

        os.environ["THALOS_HARDWARE_ID"] = "test-hardware-integration"
        self.bridge = ThalosBridge()

        # Apply schema
        try:
            self.bridge.apply_schema()
        except Exception as e:
            self.skipTest(f"Cannot connect to database: {e}")

    def tearDown(self):
        """Clean up after integration tests."""
        if "THALOS_HARDWARE_ID" in os.environ:
            del os.environ["THALOS_HARDWARE_ID"]

    def test_apply_schema(self):
        """Test that schema application succeeds."""
        # Should not raise
        self.bridge.apply_schema()

    def test_write_and_fetch_manifold_coordinate(self):
        """Test writing and fetching manifold coordinates."""
        coord_id = self.bridge.write_manifold_coordinate(
            source="test_sensor",
            coordinate={"x": 1.5, "y": -0.3},
            embedding=[0.1, 0.2, 0.3, 0.4],
            confidence=0.95,
            tags=["test", "integration"]
        )

        self.assertIsInstance(coord_id, int)
        self.assertGreater(coord_id, 0)

        # Fetch coordinates
        coords = self.bridge.fetch_manifold_coordinates(limit=10)
        self.assertIsInstance(coords, list)
        self.assertGreater(len(coords), 0)

        # Find our coordinate
        our_coord = next((c for c in coords if c["id"] == coord_id), None)
        self.assertIsNotNone(our_coord)
        self.assertEqual(our_coord["source"], "test_sensor")
        self.assertEqual(our_coord["confidence"], 0.95)

    def test_write_and_fetch_void_logs(self):
        """Test writing and fetching void logs."""
        log_id = self.bridge.write_void_log(
            severity="warn",
            message="Test warning message",
            context={"test": True, "value": 42}
        )

        self.assertIsInstance(log_id, int)
        self.assertGreater(log_id, 0)

        # Fetch logs
        logs = self.bridge.fetch_void_logs(limit=10)
        self.assertIsInstance(logs, list)
        self.assertGreater(len(logs), 0)

        # Find our log
        our_log = next((l for l in logs if l["id"] == log_id), None)
        self.assertIsNotNone(our_log)
        self.assertEqual(our_log["severity"], "warn")
        self.assertEqual(our_log["message"], "Test warning message")

    def test_write_void_log_invalid_severity(self):
        """Test that invalid severity is rejected."""
        with self.assertRaises(ValueError) as cm:
            self.bridge.write_void_log(
                severity="invalid",
                message="Test message"
            )
        self.assertIn("Invalid severity", str(cm.exception))

    def test_fetch_void_logs_with_min_severity(self):
        """Test filtering logs by minimum severity."""
        # Write logs of different severities
        self.bridge.write_void_log("debug", "Debug message")
        self.bridge.write_void_log("error", "Error message")

        # Fetch only error and fatal
        logs = self.bridge.fetch_void_logs(limit=100, min_severity="error")

        # All returned logs should be error or fatal
        for log in logs:
            self.assertIn(log["severity"], ["error", "fatal"])

    def test_upsert_and_load_encrypted_weights(self):
        """Test storing and loading encrypted weights."""
        model_name = "test-model-integration"
        weights_data = b"fake neural network weights data for testing"
        metadata = {"version": "1.0", "architecture": "test"}

        # Upsert weights
        weight_id = self.bridge.upsert_encrypted_weights(
            model_name=model_name,
            weights=weights_data,
            metadata=metadata
        )

        self.assertIsInstance(weight_id, int)
        self.assertGreater(weight_id, 0)

        # Load weights
        loaded_data = self.bridge.load_encrypted_weights(model_name)
        self.assertEqual(loaded_data, weights_data)

        # Update weights (upsert)
        updated_weights = b"updated weights data"
        weight_id2 = self.bridge.upsert_encrypted_weights(
            model_name=model_name,
            weights=updated_weights,
            metadata={"version": "2.0"}
        )

        # Should update existing record
        loaded_updated = self.bridge.load_encrypted_weights(model_name)
        self.assertEqual(loaded_updated, updated_weights)

    def test_load_nonexistent_weights_fails(self):
        """Test that loading nonexistent weights fails."""
        with self.assertRaises(ValueError) as cm:
            self.bridge.load_encrypted_weights("nonexistent-model-xyz")
        self.assertIn("No weights found", str(cm.exception))

    def test_void_log_with_coordinate_ref(self):
        """Test creating void log with coordinate reference."""
        # Create coordinate
        coord_id = self.bridge.write_manifold_coordinate(
            source="test",
            coordinate={"x": 1},
            embedding=[0.1, 0.2]
        )

        # Create log referencing coordinate
        log_id = self.bridge.write_void_log(
            severity="info",
            message="Referenced log",
            context={"coord": coord_id},
            coordinate_ref=coord_id
        )

        # Fetch and verify
        logs = self.bridge.fetch_void_logs(limit=10)
        our_log = next((l for l in logs if l["id"] == log_id), None)
        self.assertIsNotNone(our_log)
        self.assertEqual(our_log["coordinate_ref"], coord_id)


if __name__ == '__main__':
    unittest.main()
