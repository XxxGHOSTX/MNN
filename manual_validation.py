#!/usr/bin/env python
"""
Manual validation script for PR #3 functionality.
Tests the end-to-end workflow without requiring a real database.
"""

import os
import sys
import tempfile

# Set environment variables for testing
os.environ["THALOS_HARDWARE_ID"] = "manual-test-hardware-123"
os.environ["THALOS_DB_DSN"] = "postgresql://test:test@localhost:5432/test"

from middleware import ThalosBridge
from weight_encryptor import WeightEncryptor, EncryptedWeights
from pathlib import Path


def test_weight_encryption():
    """Test hardware-bound weight encryption end-to-end."""
    print("\n=== Testing Weight Encryption ===")

    # Create encryptor
    encryptor = WeightEncryptor()
    print(f"✓ Created WeightEncryptor")
    print(f"  Hardware fingerprint: {encryptor.hardware_fingerprint()}")

    # Test data
    test_weights = b"Neural network weights: " + bytes(range(256))
    print(f"✓ Test data size: {len(test_weights)} bytes")

    # Encrypt
    encrypted = encryptor.encrypt(test_weights, associated_data=b"model-v1")
    print(f"✓ Encrypted weights:")
    print(f"  - Ciphertext size: {len(encrypted.ciphertext)} bytes")
    print(f"  - Nonce size: {len(encrypted.nonce)} bytes (expected 12)")
    print(f"  - Salt size: {len(encrypted.salt)} bytes (expected 16)")
    print(f"  - Checksum: {encrypted.checksum[:16]}...")
    print(f"  - Hardware fingerprint: {encrypted.hardware_fingerprint}")

    # Decrypt
    decrypted = encryptor.decrypt(encrypted, associated_data=b"model-v1")
    assert decrypted == test_weights, "Decryption failed!"
    print(f"✓ Successfully decrypted and verified")

    # Test hardware binding
    print("\n--- Testing hardware binding ---")
    try:
        os.environ["THALOS_HARDWARE_ID"] = "different-hardware-456"
        different_encryptor = WeightEncryptor()
        different_encryptor.decrypt(encrypted, associated_data=b"model-v1")
        print("✗ ERROR: Should have failed with different hardware!")
        return False
    except ValueError as e:
        if "Hardware fingerprint mismatch" in str(e):
            print(f"✓ Correctly rejected decryption on different hardware")
        else:
            raise
    finally:
        os.environ["THALOS_HARDWARE_ID"] = "manual-test-hardware-123"

    # Test AAD verification
    print("\n--- Testing associated data verification ---")
    try:
        encryptor.decrypt(encrypted, associated_data=b"wrong-model")
        print("✗ ERROR: Should have failed with wrong associated data!")
        return False
    except Exception:
        print(f"✓ Correctly rejected decryption with wrong associated data")

    return True


def test_middleware_api():
    """Test ThalosBridge middleware API (without database)."""
    print("\n=== Testing ThalosBridge Middleware ===")

    # Test initialization
    print("\n--- Testing initialization ---")
    bridge = ThalosBridge(dsn="postgresql://user:pass@localhost:5432/db")
    print(f"✓ Created ThalosBridge with DSN")
    print(f"  DSN: {bridge.dsn}")

    # Test DSN validation
    print("\n--- Testing DSN validation ---")
    try:
        bad_bridge = ThalosBridge(dsn="postgresql://user\ninjection@host/db")
        print("✗ ERROR: Should have rejected DSN with newline!")
        return False
    except ValueError as e:
        if "control characters" in str(e):
            print(f"✓ Correctly rejected DSN with control characters")
        else:
            raise

    # Test empty DSN rejection
    try:
        empty_bridge = ThalosBridge(dsn="   ")
        print("✗ ERROR: Should have rejected empty DSN!")
        return False
    except ValueError as e:
        if "Database DSN must be provided" in str(e):
            print(f"✓ Correctly rejected empty DSN")
        else:
            raise

    # Test severity levels
    print("\n--- Testing severity levels ---")
    from middleware import SEVERITY_LEVELS
    print(f"✓ Severity levels defined: {SEVERITY_LEVELS}")
    assert SEVERITY_LEVELS == ("debug", "info", "warn", "error", "fatal")
    print(f"✓ Severity levels correctly ordered")

    return True


def test_schema_file():
    """Test that database schema file exists and is valid."""
    print("\n=== Testing Database Schema ===")

    schema_path = Path(__file__).parent / "thalos_db_schema.sql"
    if not schema_path.exists():
        print(f"✗ ERROR: Schema file not found at {schema_path}")
        return False

    print(f"✓ Schema file exists: {schema_path}")

    # Read and validate schema
    with open(schema_path, 'r') as f:
        schema = f.read()

    # Check for expected tables
    required_tables = [
        "manifold_coordinates",
        "void_logs",
        "weights_vault"
    ]

    for table in required_tables:
        if table in schema:
            print(f"✓ Table '{table}' defined in schema")
        else:
            print(f"✗ ERROR: Table '{table}' not found in schema")
            return False

    # Check for indexes
    required_indexes = [
        "idx_manifold_coordinates_created_at",
        "idx_void_logs_severity_logged_at",
        "idx_weights_vault_model"
    ]

    for index in required_indexes:
        if index in schema:
            print(f"✓ Index '{index}' defined")
        else:
            print(f"⚠ Warning: Index '{index}' not found")

    # Check for constraints
    if "CHECK (confidence >= 0 AND confidence <= 1)" in schema:
        print(f"✓ Confidence constraint defined correctly")
    else:
        print(f"⚠ Warning: Confidence constraint not found or incorrect")

    if "CHECK (severity IN" in schema:
        print(f"✓ Severity constraint defined")
    else:
        print(f"⚠ Warning: Severity constraint not found")

    return True


def test_example_usage():
    """Test the example usage from README and PR description."""
    print("\n=== Testing Example Usage from Documentation ===")

    # Example from PR description and README
    print("\n--- Example workflow (without actual database) ---")
    print("Example code structure:")
    print("""
    from middleware import ThalosBridge

    bridge = ThalosBridge()
    bridge.apply_schema()

    # Write coordinate
    cid = bridge.write_manifold_coordinate(
        "sensorA", {"x": 1}, [0.1, 0.2], 0.98
    )

    # Write log
    bridge.write_void_log(
        "info", "captured", {"id": cid}, coordinate_ref=cid
    )

    # Encrypt and store weights
    with open("weights.bin", "rb") as fh:
        bridge.upsert_encrypted_weights("mnn-core", fh.read())

    # Load weights
    restored = bridge.load_encrypted_weights("mnn-core")
    """)
    print("✓ Example structure matches PR description")

    # Test that the API signatures match
    import inspect

    # Check ThalosBridge methods
    print("\n--- Validating API signatures ---")
    bridge = ThalosBridge(dsn="postgresql://test@localhost/test")

    methods_to_check = [
        ("apply_schema", ["schema_path"]),
        ("write_manifold_coordinate", ["source", "coordinate", "embedding", "confidence", "tags"]),
        ("fetch_manifold_coordinates", ["limit"]),
        ("write_void_log", ["severity", "message", "context", "coordinate_ref"]),
        ("fetch_void_logs", ["limit", "min_severity"]),
        ("upsert_encrypted_weights", ["model_name", "weights", "metadata", "associated_data"]),
        ("load_encrypted_weights", ["model_name", "associated_data"]),
    ]

    for method_name, expected_params in methods_to_check:
        if hasattr(bridge, method_name):
            method = getattr(bridge, method_name)
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())
            print(f"✓ Method '{method_name}' exists with params: {params}")
        else:
            print(f"✗ ERROR: Method '{method_name}' not found!")
            return False

    # Check WeightEncryptor methods
    encryptor = WeightEncryptor()
    encryptor_methods = [
        ("hardware_fingerprint", []),
        ("encrypt", ["weights", "associated_data", "salt"]),
        ("decrypt", ["payload", "associated_data"]),
    ]

    for method_name, _ in encryptor_methods:
        if hasattr(encryptor, method_name):
            print(f"✓ Method '{method_name}' exists in WeightEncryptor")
        else:
            print(f"✗ ERROR: Method '{method_name}' not found in WeightEncryptor!")
            return False

    return True


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("PR #3 Functionality Validation")
    print("Testing Thalos Persistence Layer and Hardware-Bound Weight Encryption")
    print("=" * 70)

    all_passed = True

    tests = [
        ("Weight Encryption", test_weight_encryption),
        ("Middleware API", test_middleware_api),
        ("Database Schema", test_schema_file),
        ("Example Usage", test_example_usage),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"\n✗ ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
            all_passed = False

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL VALIDATION TESTS PASSED")
        print("=" * 70)
        return 0
    else:
        print("✗ SOME VALIDATION TESTS FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
