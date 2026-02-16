"""
MNN Pipeline FastAPI Application

RESTful API interface for the Matrix Neural Network (MNN) knowledge engine.
Provides a /query endpoint for external systems (like Thalos Prime) to submit
queries and receive deterministic, ranked results.
"""

import logging
from functools import lru_cache
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from main import _execute_pipeline
from mnn_pipeline import normalize_query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# FastAPI app instance
app = FastAPI(
    title="MNN Knowledge Engine API",
    description="Deterministic knowledge engine inspired by Library of Babel",
    version="1.0.0",
)


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


@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    """
    Query endpoint for MNN knowledge engine.
    
    Accepts a query and returns the top 5 most relevant results.
    Results are deterministic: the same query always produces the same output.
    
    Args:
        request: QueryRequest containing the search query
        
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
    try:
        # Validate query is not empty or whitespace-only
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Execute cached pipeline (will raise ValueError if normalized query is empty)
        try:
            results = cached_pipeline(request.query)
        except ValueError as ve:
            # Handle empty normalized pattern
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


@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        Dictionary with status information
    """
    return {
        "status": "healthy",
        "service": "MNN Knowledge Engine",
        "cache_info": {
            "pipeline_cache_size": _cached_execute_api_pipeline.cache_info().currsize,
            "pipeline_cache_hits": _cached_execute_api_pipeline.cache_info().hits,
            "pipeline_cache_misses": _cached_execute_api_pipeline.cache_info().misses,
        }
    }


if __name__ == "__main__":
    import os
    import uvicorn
    
    # Default to localhost for security, but allow override via environment variable
    host = os.getenv("MNN_API_HOST", "127.0.0.1")
    port = int(os.getenv("MNN_API_PORT", "8000"))
    
    print("Starting MNN Knowledge Engine API...")
    print(f"API will be available at: http://{host}:{port}")
    print(f"Interactive docs at: http://{host}:{port}/docs")
    print()
    if host == "0.0.0.0":
        print("⚠️  WARNING: API is binding to 0.0.0.0 (all interfaces)")
        print("   This exposes the API to the entire network without authentication.")
        print("   For production, use a proper WSGI server with security configurations.")
    
    uvicorn.run(app, host=host, port=port)
