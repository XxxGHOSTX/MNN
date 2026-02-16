"""
Tests for security module.

Tests rate limiting, security validation, and middleware functionality.
"""
import unittest
import time
from security import (
    RateLimiter,
    validate_query_security,
    generate_request_id,
    APIKeyAuth,
)
from fastapi import HTTPException


class TestRateLimiter(unittest.TestCase):
    """Test rate limiter functionality."""

    def test_rate_limiter_allows_requests_under_limit(self):
        """Test that requests under the limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        client_id = "test_client"

        # Make 5 requests (all should be allowed)
        for _ in range(5):
            self.assertTrue(limiter.is_allowed(client_id))

    def test_rate_limiter_blocks_requests_over_limit(self):
        """Test that requests over the limit are blocked."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        client_id = "test_client"

        # Make 3 requests (allowed)
        for _ in range(3):
            self.assertTrue(limiter.is_allowed(client_id))

        # 4th request should be blocked
        self.assertFalse(limiter.is_allowed(client_id))

    def test_rate_limiter_sliding_window(self):
        """Test that old requests outside the window are removed."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        client_id = "test_client"

        # Make 2 requests
        self.assertTrue(limiter.is_allowed(client_id))
        self.assertTrue(limiter.is_allowed(client_id))

        # Should be blocked
        self.assertFalse(limiter.is_allowed(client_id))

        # Wait for window to slide
        time.sleep(1.1)

        # Should be allowed again
        self.assertTrue(limiter.is_allowed(client_id))

    def test_rate_limiter_multiple_clients(self):
        """Test that rate limits are per-client."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        # Client A makes 2 requests
        self.assertTrue(limiter.is_allowed("client_a"))
        self.assertTrue(limiter.is_allowed("client_a"))
        self.assertFalse(limiter.is_allowed("client_a"))

        # Client B should still be allowed
        self.assertTrue(limiter.is_allowed("client_b"))
        self.assertTrue(limiter.is_allowed("client_b"))

    def test_rate_limiter_retry_after(self):
        """Test retry_after calculation."""
        limiter = RateLimiter(max_requests=1, window_seconds=10)
        client_id = "test_client"

        limiter.is_allowed(client_id)  # Use up the limit
        retry_after = limiter.get_retry_after(client_id)

        # Should be between 0 and 10 seconds
        self.assertGreaterEqual(retry_after, 0)
        self.assertLessEqual(retry_after, 10)


class TestQueryValidation(unittest.TestCase):
    """Test query security validation."""

    def test_validate_query_valid(self):
        """Test that valid queries pass validation."""
        # Should not raise exception
        validate_query_security("normal query", max_length=100)
        validate_query_security("query with numbers 123", max_length=100)
        validate_query_security("query-with-dashes", max_length=100)

    def test_validate_query_too_long(self):
        """Test that overly long queries are rejected."""
        long_query = "a" * 1001
        with self.assertRaises(HTTPException) as context:
            validate_query_security(long_query, max_length=1000)
        self.assertEqual(context.exception.status_code, 400)

    def test_validate_query_excessive_repetition(self):
        """Test that queries with excessive repetition are rejected."""
        repetitive_query = "a" * 1000
        with self.assertRaises(HTTPException) as context:
            validate_query_security(repetitive_query, max_length=2000)
        self.assertEqual(context.exception.status_code, 400)

    def test_validate_query_control_characters(self):
        """Test that control characters are rejected."""
        query_with_control = "normal\x00query"
        with self.assertRaises(HTTPException) as context:
            validate_query_security(query_with_control)
        self.assertEqual(context.exception.status_code, 400)

    def test_validate_query_allows_whitespace(self):
        """Test that normal whitespace is allowed."""
        # Should not raise exception
        validate_query_security("query with\ttabs\nand\rnewlines")


class TestRequestID(unittest.TestCase):
    """Test request ID generation."""

    def test_generate_request_id_unique(self):
        """Test that request IDs are unique."""
        id1 = generate_request_id()
        id2 = generate_request_id()
        self.assertNotEqual(id1, id2)

    def test_generate_request_id_format(self):
        """Test request ID format (timestamp-random)."""
        request_id = generate_request_id()
        parts = request_id.split('-')
        self.assertEqual(len(parts), 2)
        # First part should be numeric (timestamp)
        self.assertTrue(parts[0].isdigit())
        # Second part should be hex
        self.assertTrue(all(c in '0123456789abcdef' for c in parts[1]))


class TestAPIKeyAuth(unittest.TestCase):
    """Test API key authentication."""

    def test_validate_api_key_valid(self):
        """Test validation of valid API key."""
        auth = APIKeyAuth()
        result = auth.validate_api_key("demo_key")
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Demo User")

    def test_validate_api_key_invalid(self):
        """Test validation of invalid API key."""
        auth = APIKeyAuth()
        result = auth.validate_api_key("invalid_key")
        self.assertIsNone(result)

    def test_add_api_key(self):
        """Test adding new API key."""
        auth = APIKeyAuth()
        new_key = auth.add_api_key("Test User", rate_limit=50)

        # Validate the new key works
        result = auth.validate_api_key(new_key)
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Test User")
        self.assertEqual(result["rate_limit"], 50)


if __name__ == '__main__':
    unittest.main()
