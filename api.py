"""
MNN Pipeline FastAPI Application

RESTful API interface for the Matrix Neural Network (MNN) knowledge engine.
Provides a /query endpoint for external systems (like Thalos Prime) to submit
queries and receive deterministic, ranked results.
"""

import hmac
import os
from functools import lru_cache
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from main import _execute_pipeline
from mnn_pipeline import normalize_query
from config import config
from auth_utils import create_access_token, verify_access_token
from infra_status import get_infra_status
from logging_config import setup_logging, get_logger, set_request_id
from security import (
    RateLimiter,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    validate_query_security,
    generate_request_id,
)

# Configure logging
setup_logging(log_level=config.LOG_LEVEL, log_format=config.LOG_FORMAT)
logger = get_logger(__name__)


# FastAPI app instance with metadata
app = FastAPI(
    title="MNN Knowledge Engine API",
    description="Deterministic knowledge engine inspired by Library of Babel",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "query",
            "description": "Query operations for knowledge extraction",
        },
        {
            "name": "monitoring",
            "description": "Health check and monitoring endpoints",
        },
        {
            "name": "auth",
            "description": "Authentication and session management",
        },
        {
            "name": "dashboard",
            "description": "Operational dashboard endpoints",
        },
    ],
)

http_bearer = HTTPBearer(auto_error=False)

# Add CORS middleware (configure allowed origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware if enabled
if config.RATE_LIMIT_ENABLED:
    rate_limiter = RateLimiter(
        max_requests=config.RATE_LIMIT_REQUESTS,
        window_seconds=config.RATE_LIMIT_WINDOW
    )
    app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
    logger.info(
        f"Rate limiting enabled: {config.RATE_LIMIT_REQUESTS} requests per {config.RATE_LIMIT_WINDOW}s"
    )


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Add request ID to all requests for tracing."""
    request_id = generate_request_id()
    set_request_id(request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


class QueryRequest(BaseModel):
    """
    Request model for query endpoint.
    
    Attributes:
        query: The search query string (required, non-empty)
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query string (max 1000 characters)",
    )


class QueryResponse(BaseModel):
    """
    Response model for query endpoint.
    
    Attributes:
        query: The original query (normalized)
        results: List of top 5 results with sequences and scores
        count: Number of results returned
    """
    query: str = Field(..., description="Normalized query")
    results: List[Dict[str, Any]] = Field(..., description="Top ranked results")
    count: int = Field(..., description="Number of results returned")


class LoginRequest(BaseModel):
    """Authentication request model."""

    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)


class TokenResponse(BaseModel):
    """Authentication token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfileResponse(BaseModel):
    """Authenticated user profile response model."""

    username: str
    auth_enabled_for_query_endpoint: bool


class FeedbackRequest(BaseModel):
    """
    Request model for feedback endpoint.
    
    Attributes:
        query: The original query string
        result_sequence: The result sequence being rated
        rating: User rating from 1 (poor) to 5 (excellent)
        user_id: Optional user identifier
        comment: Optional text comment
    """
    query: str = Field(..., min_length=1, description="Original query")
    result_sequence: str = Field(..., min_length=1, description="Result sequence being rated")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 (poor) to 5 (excellent)")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment (max 500 chars)")


class FeedbackResponse(BaseModel):
    """
    Response model for feedback endpoint.
    
    Attributes:
        success: Whether feedback was recorded successfully
        message: Confirmation message
        feedback_id: Unique identifier for the feedback entry
    """
    success: bool
    message: str
    timestamp: str


def _cached_execute_api_pipeline(query: str) -> List[Dict[str, Any]]:
    """Internal cached pipeline execution for API. Do not call directly."""
    return _execute_pipeline(query, top_n=5)

# Apply lru_cache to the internal function
_cached_execute_api_pipeline = lru_cache(maxsize=256)(_cached_execute_api_pipeline)


def cached_pipeline(query: str) -> List[Dict[str, Any]]:
    """
    Cached wrapper for the MNN pipeline.
    
    This function provides deterministic caching for API queries, ensuring
    that identical queries return identical results without recomputation.
    The cache is transparent and doesn't affect determinism.
    
    Note: Returns a deep copy of cached results to prevent cache corruption from mutations.
    Each call returns a fresh deep copy, so mutations to returned values don't affect
    the cache.
    
    Args:
        query: The user's search query
        
    Returns:
        List of top 5 ranked results (deep copy to prevent cache corruption)
    """
    # Get cached result and return a deep copy
    # Deep copy happens on every call, not just on cache miss
    import copy
    return copy.deepcopy(_cached_execute_api_pipeline(query))


def _get_auth_secret() -> str:
    """Return configured auth secret with safe local fallback."""
    return config.MNN_AUTH_SECRET or "mnn-dev-secret-change-me"


def _authenticate_user(username: str, password: str) -> bool:
    """Validate credentials against configured admin account."""
    return hmac.compare_digest(username, config.MNN_ADMIN_USERNAME) and hmac.compare_digest(
        password,
        config.MNN_ADMIN_PASSWORD,
    )


def _validate_bearer_token(credentials: Optional[HTTPAuthorizationCredentials]) -> Dict[str, Any]:
    """Validate bearer token and return decoded payload."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_access_token(credentials.credentials, _get_auth_secret())
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer)) -> Dict[str, Any]:
    """Dependency returning current authenticated user."""
    payload = _validate_bearer_token(credentials)
    return {"username": payload.get("sub", "unknown")}


@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login(request: LoginRequest):
    """Authenticate operator and issue bearer token."""
    if not _authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        username=request.username,
        secret=_get_auth_secret(),
        expires_minutes=config.MNN_TOKEN_EXPIRE_MINUTES,
    )
    return TokenResponse(
        access_token=token,
        expires_in=config.MNN_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.get("/auth/me", response_model=UserProfileResponse, tags=["auth"])
def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return profile information for currently authenticated operator."""
    return UserProfileResponse(
        username=current_user["username"],
        auth_enabled_for_query_endpoint=config.API_AUTH_ENABLED,
    )


@app.get("/")
def root():
    """
    Root endpoint providing API information.
    
    Returns:
        Dictionary with API name, version, and usage instructions
    """
    return {
        "name": "MNN Knowledge Engine API",
        "version": "1.0.0",
        "description": "Deterministic knowledge engine inspired by Library of Babel",
        "endpoints": {
            "/query": "POST endpoint for submitting queries",
            "/docs": "Interactive API documentation",
            "/auth/login": "POST operator login",
            "/dashboard/overview": "GET authenticated dashboard data",
        },
        "example": {
            "curl": 'curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d \'{"query":"artificial intelligence"}\'',
            "python": 'import requests; response = requests.post("http://localhost:8000/query", json={"query": "artificial intelligence"})',
        }
    }


@app.post("/query", response_model=QueryResponse, tags=["query"])
def query_endpoint(request: QueryRequest, http_request: Request):
    """
    Query endpoint for MNN knowledge engine.

    Accepts a query and returns the top 5 most relevant results.
    Results are deterministic: the same query always produces the same output.

    Args:
        request: QueryRequest containing the search query
        http_request: HTTP request for logging

    Returns:
        QueryResponse with normalized query, top 5 results, and count

    Raises:
        HTTPException:
            - 400 if query is empty or invalid
            - 500 if pipeline execution fails

    Examples:
        POST /query
        {
            "query": "artificial intelligence"
        }

        Response:
        {
            "query": "ARTIFICIAL INTELLIGENCE",
            "results": [
                {
                    "sequence": "BOOK 0: ARTIFICIAL INTELLIGENCE CONTINUES...",
                    "score": 0.98
                },
                ...
            ],
            "count": 5
        }
    """
    import time
    from metrics import get_metrics_collector, track_slow_query
    
    metrics = get_metrics_collector()
    start_time = time.time()
    
    client_host = http_request.client.host if http_request.client else "unknown"
    logger.info(f"Received query from {client_host}: {request.query[:100]}")

    if config.API_AUTH_ENABLED:
        auth_header = http_request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "", 1) if auth_header.startswith("Bearer ") else ""
        if not token or verify_access_token(token, _get_auth_secret()) is None:
            metrics.increment_counter('mnn_queries_error_total', labels={'error_type': 'auth_required'})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for query endpoint",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Increment total queries
    metrics.increment_counter('mnn_queries_total')

    try:
        # Validate query is not empty or whitespace-only
        if not request.query or not request.query.strip():
            logger.warning(f"Empty query from {client_host}")
            metrics.increment_counter('mnn_queries_error_total', labels={'error_type': 'empty_query'})
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Security validation
        validate_query_security(request.query, max_length=config.MAX_QUERY_LENGTH)

        # Execute cached pipeline (will raise ValueError if normalized query is empty)
        try:
            results = cached_pipeline(request.query)
            logger.info(f"Query processed successfully, returned {len(results)} results")
            
            # Track success
            duration = time.time() - start_time
            metrics.observe_histogram('mnn_query_duration_seconds', duration, {'status': 'success'})
            metrics.increment_counter('mnn_queries_success_total')
            
            # Check for slow queries
            track_slow_query(request.query, duration, threshold=1.0)
            
        except ValueError as ve:
            # Handle empty normalized pattern
            logger.warning(f"Invalid query after normalization: {ve}")
            duration = time.time() - start_time
            metrics.observe_histogram('mnn_query_duration_seconds', duration, {'status': 'error'})
            metrics.increment_counter('mnn_queries_error_total', labels={'error_type': 'validation_error'})
            raise HTTPException(status_code=400, detail=str(ve))

        # Get normalized query for response
        normalized = normalize_query(request.query)

        # Build response
        return QueryResponse(
            query=normalized,
            results=results,
            count=len(results)
        )

    except HTTPException as he:
        # Track HTTP errors (but don't double-count validation errors)
        if he.status_code != 400:
            duration = time.time() - start_time
            metrics.observe_histogram('mnn_query_duration_seconds', duration, {'status': 'error'})
            metrics.increment_counter('mnn_queries_error_total', labels={'error_type': f'http_{he.status_code}'})
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the full exception internally for debugging
        logger.error(f"Pipeline execution failed for query: {request.query}", exc_info=True)
        
        # Track unexpected errors
        duration = time.time() - start_time
        metrics.observe_histogram('mnn_query_duration_seconds', duration, {'status': 'error'})
        metrics.increment_counter('mnn_queries_error_total', labels={'error_type': type(e).__name__})
        
        # Return generic error message to client
        raise HTTPException(
            status_code=500,
            detail="Pipeline execution failed. Please try again or contact support."
        )


@app.get("/health", tags=["monitoring"])
def health_check():
    """
    Health check endpoint for monitoring.

    Checks application health including database connectivity and cache status.

    Returns:
        Dictionary with status information including:
        - status: overall health status
        - service: service name
        - version: API version
        - database: database connectivity status
        - cache_info: cache statistics
        - uptime_seconds: time since startup
    """
    from datetime import datetime
    import time
    
    # Calculate uptime (using app startup time if available)
    if not hasattr(app.state, 'start_time'):
        app.state.start_time = time.time()
    uptime = time.time() - app.state.start_time
    
    health_status = {
        "status": "healthy",
        "service": "MNN Knowledge Engine",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": int(uptime),
        "cache_info": {
            "pipeline_cache_size": _cached_execute_api_pipeline.cache_info().currsize,
            "pipeline_cache_hits": _cached_execute_api_pipeline.cache_info().hits,
            "pipeline_cache_misses": _cached_execute_api_pipeline.cache_info().misses,
            "pipeline_cache_maxsize": _cached_execute_api_pipeline.cache_info().maxsize,
        }
    }

    # Check database connectivity if DSN is configured
    if config.THALOS_DB_DSN:
        try:
            from middleware import ThalosBridge
            bridge = ThalosBridge()
            with bridge.connection():
                # Simple connectivity check
                health_status["database"] = "connected"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_status["database"] = "disconnected"
            health_status["status"] = "degraded"
    else:
        health_status["database"] = "not_configured"

    return health_status


@app.get("/dashboard/overview", tags=["dashboard"])
def dashboard_overview(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Provide authenticated dashboard data with graceful infra fallbacks."""
    from datetime import datetime
    from feedback import get_feedback_store
    from metrics import get_metrics_collector

    metrics_data = get_metrics_collector().get_metrics()
    counters = metrics_data.get("counters", {})
    histograms = metrics_data.get("histograms", {})
    query_duration = histograms.get("mnn_query_duration_seconds{status=\"success\"}", {})

    total_queries = sum(
        value for key, value in counters.items() if key.startswith("mnn_queries_total")
    )
    total_errors = sum(
        value for key, value in counters.items() if key.startswith("mnn_queries_error_total")
    )
    total_success = sum(
        value for key, value in counters.items() if key.startswith("mnn_queries_success_total")
    )

    infra = get_infra_status(config)
    feedback_stats = get_feedback_store().get_statistics()

    return {
        "timestamp": datetime.now().isoformat(),
        "user": current_user["username"],
        "health": health_check(),
        "metrics": {
            "total_queries": total_queries,
            "total_success": total_success,
            "total_errors": total_errors,
            "avg_latency_seconds": round(query_duration.get("avg", 0), 4),
            "cache": {
                "hits": _cached_execute_api_pipeline.cache_info().hits,
                "misses": _cached_execute_api_pipeline.cache_info().misses,
                "size": _cached_execute_api_pipeline.cache_info().currsize,
            },
        },
        "infra": infra,
        "feedback": feedback_stats,
    }


@app.get("/infra/status", tags=["dashboard"])
def infra_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Expose infrastructure status as a dedicated endpoint."""
    return {
        "user": current_user["username"],
        "services": get_infra_status(config),
    }


@app.get("/metrics", tags=["monitoring"])
def metrics_endpoint():
    """
    Prometheus-compatible metrics endpoint.
    
    Exposes application metrics in Prometheus text format for monitoring
    and alerting. Metrics include:
    - Query counts (total, success, errors)
    - Query duration histograms
    - Cache performance (hits, misses, size)
    - Slow query counts
    
    Returns:
        Plain text response in Prometheus exposition format
        
    Example metrics:
        # TYPE mnn_queries_total counter
        mnn_queries_total 1234
        
        # TYPE mnn_query_duration_seconds histogram
        mnn_query_duration_seconds_count{status="success"} 1200
        mnn_query_duration_seconds_sum{status="success"} 45.2
        
        # TYPE mnn_cache_hit_rate gauge
        mnn_cache_hit_rate 0.85
    """
    from fastapi.responses import PlainTextResponse
    from metrics import get_metrics_collector, update_cache_metrics
    
    # Update cache metrics before export
    cache_info = _cached_execute_api_pipeline.cache_info()
    update_cache_metrics(cache_info)
    
    # Get metrics collector
    metrics = get_metrics_collector()
    
    # Export in Prometheus format
    prometheus_text = metrics.export_prometheus()
    
    return PlainTextResponse(prometheus_text, media_type="text/plain; version=0.0.4")


@app.get("/api/version", tags=["monitoring"])
def version_info():
    """
    Get API version information.
    
    Returns detailed version information including:
    - API version
    - Pipeline version
    - Deployment environment
    - Feature flags
    
    Returns:
        Dictionary with version details
    """
    return {
        "api_version": "1.0.0",
        "pipeline_version": "1.0.0",
        "environment": config.ENVIRONMENT if hasattr(config, 'ENVIRONMENT') else "production",
        "features": {
            "rate_limiting": config.RATE_LIMIT_ENABLED,
            "authentication": config.API_AUTH_ENABLED,
            "operator_auth": True,
            "database": bool(config.THALOS_DB_DSN),
            "redis": bool(config.REDIS_URL),
            "minio": bool(config.MINIO_ENDPOINT),
            "keycloak": bool(config.KEYCLOAK_URL),
            "query_classification": True,
            "synonym_expansion": True,
            "user_feedback": True,
        }
    }


@app.post("/feedback", response_model=FeedbackResponse, tags=["feedback"])
def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback for a query result.
    
    Allows users to rate results and provide comments, enabling the system
    to track result quality and suggest improvements over time.
    
    Args:
        request: FeedbackRequest with query, result, rating, and optional comment
        
    Returns:
        FeedbackResponse with confirmation
        
    Raises:
        HTTPException 400: Invalid rating or empty fields
        HTTPException 500: Failed to store feedback
        
    Example:
        POST /feedback
        {
            "query": "quantum computing",
            "result_sequence": "BOOK 0: QUANTUM COMPUTING...",
            "rating": 5,
            "user_id": "user123",
            "comment": "Very helpful result"
        }
    """
    from feedback import get_feedback_store
    from datetime import datetime
    
    try:
        store = get_feedback_store()
        entry = store.add_feedback(
            query=request.query,
            result_sequence=request.result_sequence,
            rating=request.rating,
            user_id=request.user_id,
            comment=request.comment
        )
        
        logger.info(
            f"Feedback submitted for query: {request.query[:50]}",
            extra={'rating': request.rating, 'user_id': request.user_id}
        )
        
        return FeedbackResponse(
            success=True,
            message="Feedback recorded successfully",
            timestamp=entry['timestamp']
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to store feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to store feedback. Please try again."
        )


@app.get("/feedback/stats", tags=["feedback"])
def feedback_statistics():
    """
    Get overall feedback statistics.
    
    Returns aggregated statistics about user feedback including:
    - Total feedback count
    - Average ratings
    - Rating distribution
    - Number of unique queries rated
    
    Returns:
        Dictionary with feedback statistics
        
    Example response:
        {
            "total_feedback": 150,
            "unique_queries": 42,
            "average_rating": 4.2,
            "rating_distribution": {
                "1": 5,
                "2": 10,
                "3": 20,
                "4": 50,
                "5": 65
            }
        }
    """
    from feedback import get_feedback_store
    
    store = get_feedback_store()
    stats = store.get_statistics()
    
    return stats


@app.get("/suggestions", tags=["feedback"])
def query_suggestions(query: str = Query(..., min_length=1, description="Current query")):
    """
    Get query suggestions based on feedback history.
    
    Suggests similar queries that have high ratings, useful for
    query refinement and discovery of related topics.
    
    Args:
        query: The current query string (query parameter)
        
    Returns:
        Dictionary with suggested queries and their ratings
        
    Example:
        GET /suggestions?query=quantum%20computing
        
        Response:
        {
            "original_query": "quantum computing",
            "suggestions": [
                {
                    "suggested_query": "quantum entanglement",
                    "average_rating": 4.8,
                    "feedback_count": 15,
                    "word_overlap": 1
                },
                ...
            ]
        }
    """
    from feedback import suggest_similar_queries
    
    suggestions = suggest_similar_queries(query, max_suggestions=5)
    
    return {
        "original_query": query,
        "suggestions": suggestions
    }


@app.get("/query/performance", tags=["feedback"])
def query_performance(query: str = Query(..., min_length=1, description="Query to analyze")):
    """
    Analyze query performance based on user feedback.
    
    Provides insights into how well a query performs based on historical
    user ratings and suggests improvements if available.
    
    Args:
        query: The query string to analyze
        
    Returns:
        Dictionary with performance metrics and suggestions
        
    Example:
        GET /query/performance?query=artificial%20intelligence
        
        Response:
        {
            "query": "artificial intelligence",
            "average_rating": 4.5,
            "total_feedback": 25,
            "positive_ratio": 88.0,
            "top_rated_results": 3,
            "suggestions": [...]
        }
    """
    from feedback import analyze_query_performance
    
    analysis = analyze_query_performance(query)
    
    return analysis


if __name__ == "__main__":
    import uvicorn

    # Validate configuration
    config.validate()

    # Log startup configuration
    logger.info("Starting MNN Knowledge Engine API")
    logger.info(f"Host: {config.MNN_API_HOST}, Port: {config.MNN_API_PORT}")
    logger.info(f"Max query length: {config.MAX_QUERY_LENGTH}")
    logger.info(f"Rate limiting: {'enabled' if config.RATE_LIMIT_ENABLED else 'disabled'}")

    print("Starting MNN Knowledge Engine API...")
    print(f"API will be available at: http://{config.MNN_API_HOST}:{config.MNN_API_PORT}")
    print(f"Interactive docs at: http://{config.MNN_API_HOST}:{config.MNN_API_PORT}/docs")
    print()

    if config.MNN_API_HOST == "0.0.0.0":
        print("⚠️  WARNING: API is binding to 0.0.0.0 (all interfaces)")
        print("   This exposes the API to the entire network.")
        print("   Ensure proper firewall and network security configurations.")

    uvicorn.run(app, host=config.MNN_API_HOST, port=config.MNN_API_PORT)
