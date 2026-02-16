"""
Tests for logging_config module.

Tests structured logging and request ID tracking.
"""
import unittest
import logging
import json
from io import StringIO
from logging_config import (
    StructuredFormatter,
    TextFormatter,
    setup_logging,
    get_logger,
    set_request_id,
    get_request_id,
)


class TestStructuredFormatter(unittest.TestCase):
    """Test JSON structured logging formatter."""

    def test_structured_formatter_basic(self):
        """Test basic JSON log formatting."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.funcName = "test_func"

        output = formatter.format(record)
        log_data = json.loads(output)

        self.assertEqual(log_data["level"], "INFO")
        self.assertEqual(log_data["logger"], "test")
        self.assertEqual(log_data["message"], "Test message")
        self.assertEqual(log_data["module"], "test_module")
        self.assertEqual(log_data["function"], "test_func")
        self.assertEqual(log_data["line"], 42)

    def test_structured_formatter_with_request_id(self):
        """Test that request ID is included when set."""
        formatter = StructuredFormatter()
        set_request_id("test-request-id")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.module = "test"
        record.funcName = "test"

        output = formatter.format(record)
        log_data = json.loads(output)

        self.assertEqual(log_data["request_id"], "test-request-id")


class TestTextFormatter(unittest.TestCase):
    """Test human-readable text formatter."""

    def test_text_formatter_basic(self):
        """Test basic text log formatting."""
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_func"

        output = formatter.format(record)

        self.assertIn("INFO", output)
        self.assertIn("test:test_func:42", output)
        self.assertIn("Test message", output)

    def test_text_formatter_with_request_id(self):
        """Test that request ID is included when set."""
        formatter = TextFormatter()
        set_request_id("test-request-123")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test"

        output = formatter.format(record)
        self.assertIn("[test-request-123]", output)


class TestLoggingSetup(unittest.TestCase):
    """Test logging configuration."""

    def test_setup_logging_json(self):
        """Test setup with JSON format."""
        setup_logging(log_level="INFO", log_format="json")
        logger = logging.getLogger()

        self.assertEqual(logger.level, logging.INFO)
        self.assertEqual(len(logger.handlers), 1)
        self.assertIsInstance(logger.handlers[0].formatter, StructuredFormatter)

    def test_setup_logging_text(self):
        """Test setup with text format."""
        setup_logging(log_level="DEBUG", log_format="text")
        logger = logging.getLogger()

        self.assertEqual(logger.level, logging.DEBUG)
        self.assertEqual(len(logger.handlers), 1)
        self.assertIsInstance(logger.handlers[0].formatter, TextFormatter)

    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test_logger")
        self.assertEqual(logger.name, "test_logger")


class TestRequestIDTracking(unittest.TestCase):
    """Test request ID context tracking."""

    def test_set_and_get_request_id(self):
        """Test setting and getting request ID."""
        test_id = "test-id-456"
        set_request_id(test_id)
        self.assertEqual(get_request_id(), test_id)

    def test_request_id_default(self):
        """Test default request ID when not set."""
        # Clear any existing request ID
        set_request_id("")
        self.assertEqual(get_request_id(), "")


if __name__ == '__main__':
    unittest.main()
