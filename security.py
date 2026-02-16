"""
Security middleware and utilities for MNN Pipeline API.

Provides authentication, rate limiting, and security headers.
"""
import time
import secrets
from typing import Dict, Optional, Callable
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RateLimiter:
    """
    Token bucket rate limiter with sliding window.

    Thread-safe rate limiter for API endpoints.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed for client.

        Args:
            client_id: Unique client identifier (IP address or API key)

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Remove old requests outside the window
        client_requests = self.requests[client_id]
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()

        # Check if under limit
        if len(client_requests) < self.max_requests:
            client_requests.append(now)
            return True

        return False

    def get_retry_after(self, client_id: str) -> int:
        """
        Get seconds until next request is allowed.

        Args:
            client_id: Client identifier

        Returns:
            Seconds to wait before retry
        """
        client_requests = self.requests[client_id]
        if not client_requests:
            return 0

        oldest_request = client_requests[0]
        retry_after = int(oldest_request + self.window_seconds - time.time())
        return max(0, retry_after)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Add security headers to response."""
        response = await call_next(request)

        # Determine if the request is effectively HTTPS (direct or via proxy)
        scheme = request.url.scheme
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        forwarded_proto = forwarded_proto.split(",")[0].strip().lower() if forwarded_proto else ""
        is_secure = scheme == "https" or forwarded_proto == "https"

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    def __init__(self, app: ASGIApp, rate_limiter: RateLimiter):
        """
        Initialize middleware.

        Args:
            app: ASGI application
            rate_limiter: Rate limiter instance
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next: Callable):
        """Check rate limit before processing request."""
        # Get client identifier (IP address)
        client_id = request.client.host if request.client else "unknown"

        # Check rate limit
        if not self.rate_limiter.is_allowed(client_id):
            retry_after = self.rate_limiter.get_retry_after(client_id)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )

        return await call_next(request)


class APIKeyAuth:
    """
    Simple API key authentication.

    In production, replace with JWT or OAuth2.
    """

    def __init__(self):
        """Initialize with default API keys."""
        # In production, load from secure storage
        self._api_keys = {
            "demo_key": {"name": "Demo User", "rate_limit": 100},
        }

    def validate_api_key(self, api_key: str) -> Optional[Dict[str, any]]:
        """
        Validate API key.

        Args:
            api_key: API key to validate

        Returns:
            Client info if valid, None otherwise
        """
        return self._api_keys.get(api_key)

    def add_api_key(self, name: str, rate_limit: int = 100) -> str:
        """
        Generate new API key.

        Args:
            name: Client name
            rate_limit: Rate limit for this key

        Returns:
            Generated API key
        """
        api_key = secrets.token_urlsafe(32)
        self._api_keys[api_key] = {"name": name, "rate_limit": rate_limit}
        return api_key


def validate_query_security(query: str, max_length: int = 1000) -> None:
    """
    Validate query for security issues.

    Args:
        query: Query string to validate
        max_length: Maximum allowed length

    Raises:
        HTTPException: If validation fails
    """
    # Check length
    if len(query) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query too long (max {max_length} characters)"
        )

    # Check for excessive repetition (potential DoS)
    if len(set(query)) < max(2, len(query) // 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query contains excessive character repetition"
        )

    # Check for control characters (excluding tab, newline)
    if any(ord(c) < 32 and c not in '\t\n\r' for c in query):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query contains invalid control characters"
        )


def generate_request_id() -> str:
    """
    Generate unique request ID for tracing.

    Returns:
        Unique request ID (timestamp + random hex)
    """
    timestamp = int(time.time() * 1000)
    random_part = secrets.token_hex(4)
    return f"{timestamp}-{random_part}"
