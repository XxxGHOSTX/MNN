"""
Tests for config module.

Tests configuration loading and validation.
"""
import unittest
import os


class TestConfigDefaults(unittest.TestCase):
    """Test configuration defaults."""

    def test_config_defaults(self):
        """Test that default values are set correctly."""
        # Clear env vars that might interfere
        old_values = {}
        env_vars = [
            'MNN_API_HOST', 'MNN_API_PORT', 'MAX_QUERY_LENGTH',
            'RATE_LIMIT_ENABLED', 'LOG_LEVEL', 'CACHE_SIZE'
        ]

        for var in env_vars:
            old_values[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        try:
            # Import fresh config after clearing env
            from config import Config
            config = Config()

            self.assertEqual(config.MNN_API_HOST, "127.0.0.1")
            self.assertEqual(config.MNN_API_PORT, 8000)
            self.assertEqual(config.MAX_QUERY_LENGTH, 1000)
            self.assertFalse(config.RATE_LIMIT_ENABLED)
            self.assertEqual(config.LOG_LEVEL, "INFO")
            self.assertEqual(config.CACHE_SIZE, 256)
        finally:
            # Restore env vars
            for var, value in old_values.items():
                if value is not None:
                    os.environ[var] = value


class TestConfigValidation(unittest.TestCase):
    """Test configuration validation."""

    def test_config_validate_valid(self):
        """Test that valid configuration passes validation."""
        from config import Config

        # Create a new config class with valid values
        class TestConfig(Config):
            MNN_API_PORT = 8000
            MAX_QUERY_LENGTH = 1000
            THALOS_DB_CONNECT_TIMEOUT = 10

        # Should not raise exception
        try:
            TestConfig.validate()
        except ValueError:
            self.fail("Valid config should not raise ValueError")

    def test_config_validate_invalid_port_too_high(self):
        """Test that invalid port (too high) raises error."""
        from config import Config

        class TestConfig(Config):
            MNN_API_PORT = 70000  # Invalid port

        with self.assertRaises(ValueError) as context:
            TestConfig.validate()
        self.assertIn("MNN_API_PORT", str(context.exception))

    def test_config_validate_invalid_port_too_low(self):
        """Test that invalid port (too low) raises error."""
        from config import Config

        class TestConfig(Config):
            MNN_API_PORT = 0  # Invalid port

        with self.assertRaises(ValueError) as context:
            TestConfig.validate()
        self.assertIn("MNN_API_PORT", str(context.exception))

    def test_config_validate_invalid_query_length(self):
        """Test that invalid query length raises error."""
        from config import Config

        class TestConfig(Config):
            MAX_QUERY_LENGTH = 0  # Invalid

        with self.assertRaises(ValueError) as context:
            TestConfig.validate()
        self.assertIn("MAX_QUERY_LENGTH", str(context.exception))

    def test_config_validate_invalid_timeout(self):
        """Test that invalid timeout raises error."""
        from config import Config

        class TestConfig(Config):
            THALOS_DB_CONNECT_TIMEOUT = 0  # Invalid

        with self.assertRaises(ValueError) as context:
            TestConfig.validate()
        self.assertIn("THALOS_DB_CONNECT_TIMEOUT", str(context.exception))


if __name__ == '__main__':
    unittest.main()
