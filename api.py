"""
MNN Pipeline FastAPI Application

RESTful API interface for the Matrix Neural Network (MNN) knowledge engine.
Provides a /query endpoint for external systems (like Thalos Prime) to submit
queries and receive deterministic, ranked results.
"""

import os
from functools import lru_cache
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from main import _execute_pipeline
from mnn_pipeline import normalize_query
from config import config
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
    ],
)

# Add CORS middleware (configure allowed origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
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
    client_host = http_request.client.host if http_request.client else "unknown"
    logger.info(f"Received query from {client_host}: {request.query[:100]}")

    try:
        # Validate query is not empty or whitespace-only
        if not request.query or not request.query.strip():
            logger.warning(f"Empty query from {client_host}")
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Security validation
        validate_query_security(request.query, max_length=config.MAX_QUERY_LENGTH)

        # Execute cached pipeline (will raise ValueError if normalized query is empty)
        try:
            results = cached_pipeline(request.query)
            logger.info(f"Query processed successfully, returned {len(results)} results")
        except ValueError as ve:
            # Handle empty normalized pattern
            logger.warning(f"Invalid query after normalization: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))

        # Get normalized query for response
        normalized = normalize_query(request.query)

        # Build response
        return QueryResponse(
            query=normalized,
            results=results,
            count=len(results)
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the full exception internally for debugging
        logger.error(f"Pipeline execution failed for query: {request.query}", exc_info=True)
        # Return generic error message to client
        raise HTTPException(
            status_code=500,
            detail="Pipeline execution failed. Please try again or contact support."
        )


@app.get("/health", tags=["monitoring"])
def health_check():
    """
    Health check endpoint for monitoring.

    Checks application health including database connectivity.

    Returns:
        Dictionary with status information including:
        - status: overall health status
        - service: service name
        - database: database connectivity status
        - cache_info: cache statistics
    """
    health_status = {
        "status": "healthy",
        "service": "MNN Knowledge Engine",
        "cache_info": {
            "pipeline_cache_size": _cached_execute_api_pipeline.cache_info().currsize,
            "pipeline_cache_hits": _cached_execute_api_pipeline.cache_info().hits,
            "pipeline_cache_misses": _cached_execute_api_pipeline.cache_info().misses,
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


if __name__ == "__main__":
    import uvicorn

    # Validate configuration
    config.validate()

    # Log startup configuration
    logger.info(f"Starting MNN Knowledge Engine API")
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
