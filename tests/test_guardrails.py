"""
Unit tests for Guardrails Module

Tests input validation, length enforcement, character checking, and error sanitization.
"""

import unittest

from guardrails import (
    ValidationError,
    validate_query_length,
    validate_query_characters,
    validate_max_results,
    validate_normalized_query,
    sanitize_error_message,
    enforce_output_limits,
    validate_full_query,
)


class TestGuardrails(unittest.TestCase):
    """Test cases for guardrails module."""
    
    def test_validate_query_length_valid(self):
        """Test query length validation with valid inputs."""
        # Should not raise
        validate_query_length("test", min_length=1, max_length=100)
        validate_query_length("a" * 50, min_length=1, max_length=100)
        validate_query_length("a", min_length=1, max_length=1)
    
    def test_validate_query_length_too_short(self):
        """Test query length validation with too-short input."""
        with self.assertRaises(ValidationError) as cm:
            validate_query_length("", min_length=1, max_length=100)
        
        self.assertIn("too short", str(cm.exception).lower())
        self.assertIn("minimum", str(cm.exception).lower())
    
    def test_validate_query_length_too_long(self):
        """Test query length validation with too-long input."""
        with self.assertRaises(ValidationError) as cm:
            validate_query_length("a" * 101, min_length=1, max_length=100)
        
        self.assertIn("too long", str(cm.exception).lower())
        self.assertIn("maximum", str(cm.exception).lower())
    
    def test_validate_query_characters_valid(self):
        """Test character validation with valid inputs."""
        # Should not raise
        validate_query_characters("Hello World!")
        validate_query_characters("Test 123")
        validate_query_characters("What is AI?")
        validate_query_characters("Machine learning, deep learning")
    
    def test_validate_query_characters_invalid(self):
        """Test character validation with invalid characters."""
        with self.assertRaises(ValidationError) as cm:
            validate_query_characters("test<script>")
        
        self.assertIn("invalid characters", str(cm.exception).lower())
        
        with self.assertRaises(ValidationError):
            validate_query_characters("test\x00null")
    
    def test_validate_query_characters_custom_pattern(self):
        """Test character validation with custom pattern."""
        # Custom pattern: only lowercase letters
        pattern = r'^[a-z]+$'
        
        # Should pass
        validate_query_characters("test", allowed_pattern=pattern)
        
        # Should fail (has uppercase)
        with self.assertRaises(ValidationError):
            validate_query_characters("Test", allowed_pattern=pattern)
        
        # Should fail (has spaces)
        with self.assertRaises(ValidationError):
            validate_query_characters("test query", allowed_pattern=pattern)
    
    def test_validate_max_results_valid(self):
        """Test max_results validation with valid inputs."""
        # Should not raise
        validate_max_results(1, upper_limit=100)
        validate_max_results(50, upper_limit=100)
        validate_max_results(100, upper_limit=100)
    
    def test_validate_max_results_too_low(self):
        """Test max_results validation with too-low value."""
        with self.assertRaises(ValidationError) as cm:
            validate_max_results(0, upper_limit=100)
        
        self.assertIn("at least 1", str(cm.exception).lower())
    
    def test_validate_max_results_too_high(self):
        """Test max_results validation with too-high value."""
        with self.assertRaises(ValidationError) as cm:
            validate_max_results(101, upper_limit=100)
        
        self.assertIn("maximum", str(cm.exception).lower())
    
    def test_validate_normalized_query_valid(self):
        """Test normalized query validation with valid input."""
        # Should not raise
        validate_normalized_query("TEST QUERY")
        validate_normalized_query("A")
        validate_normalized_query("   TRIMMED   ")
    
    def test_validate_normalized_query_empty(self):
        """Test normalized query validation with empty input."""
        with self.assertRaises(ValidationError) as cm:
            validate_normalized_query("")
        
        self.assertIn("empty", str(cm.exception).lower())
        
        with self.assertRaises(ValidationError):
            validate_normalized_query("   ")
    
    def test_sanitize_error_message_paths(self):
        """Test error message sanitization removes paths."""
        message = "Error in file /home/user/project/file.py"
        sanitized = sanitize_error_message(message)
        
        self.assertNotIn("/home/user", sanitized)
        self.assertIn("[PATH]", sanitized)
    
    def test_sanitize_error_message_ips(self):
        """Test error message sanitization removes IPs."""
        message = "Connection to 192.168.1.1 failed"
        sanitized = sanitize_error_message(message)
        
        self.assertNotIn("192.168.1.1", sanitized)
        self.assertIn("[IP]", sanitized)
    
    def test_sanitize_error_message_truncation(self):
        """Test error message sanitization truncates long messages."""
        message = "A" * 300
        sanitized = sanitize_error_message(message, max_length=200)
        
        self.assertLessEqual(len(sanitized), 203)  # 200 + "..."
        self.assertTrue(sanitized.endswith("..."))
    
    def test_enforce_output_limits_valid(self):
        """Test output limit enforcement with valid data."""
        sequences = [
            {"sequence": "test1", "score": 1.0},
            {"sequence": "test2", "score": 0.9},
        ]
        
        result = enforce_output_limits(sequences, max_sequences=10, max_sequence_length=100)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["sequence"], "test1")
    
    def test_enforce_output_limits_truncate_count(self):
        """Test output limit enforcement truncates excessive sequences."""
        # Use 15 sequences (1.5x limit, won't raise error)
        sequences = [{"sequence": f"test{i}", "score": 1.0} for i in range(15)]
        
        result = enforce_output_limits(sequences, max_sequences=10)
        
        self.assertEqual(len(result), 10)
    
    def test_enforce_output_limits_truncate_length(self):
        """Test output limit enforcement truncates long sequences."""
        long_seq = "A" * 200
        sequences = [{"sequence": long_seq, "score": 1.0}]
        
        result = enforce_output_limits(sequences, max_sequence_length=100)
        
        self.assertLessEqual(len(result[0]["sequence"]), 103)  # 100 + "..."
        self.assertTrue(result[0]["sequence"].endswith("..."))
    
    def test_enforce_output_limits_excessive_error(self):
        """Test output limit enforcement raises error for extreme excess."""
        # More than 2x max_sequences
        sequences = [{"sequence": "test", "score": 1.0} for i in range(2001)]
        
        with self.assertRaises(ValidationError) as cm:
            enforce_output_limits(sequences, max_sequences=1000)
        
        self.assertIn("too many", str(cm.exception).lower())
    
    def test_validate_full_query_valid(self):
        """Test full query validation with valid input."""
        # Should not raise
        validate_full_query("Hello World!", min_length=1, max_length=100)
        validate_full_query("Test 123", min_length=1, max_length=100)
    
    def test_validate_full_query_invalid_length(self):
        """Test full query validation catches length errors."""
        with self.assertRaises(ValidationError):
            validate_full_query("", min_length=1, max_length=100)
        
        with self.assertRaises(ValidationError):
            validate_full_query("A" * 101, min_length=1, max_length=100)
    
    def test_validate_full_query_invalid_characters(self):
        """Test full query validation catches character errors."""
        with self.assertRaises(ValidationError):
            validate_full_query("test<script>", min_length=1, max_length=100)


if __name__ == '__main__':
    unittest.main()
