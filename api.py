"""
MNN Pipeline FastAPI Application

RESTful API interface for the Matrix Neural Network (MNN) knowledge engine.
Provides a /query endpoint for external systems (like Thalos Prime) to submit
queries and receive deterministic, ranked results.
"""

from functools import lru_cache
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mnn_pipeline import (
    normalize_query,
    generate_constraints,
    map_constraints_to_indices,
    generate_sequences,
    analyze_sequences,
    score_and_rank,
)


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
    query: str = Field(..., min_length=1, description="Search query string")


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


@lru_cache(maxsize=256)
def cached_pipeline(query: str) -> List[Dict[str, Any]]:
    """
    Cached wrapper for the MNN pipeline.
    
    This function provides deterministic caching for API queries, ensuring
    that identical queries return identical results without recomputation.
    The cache is transparent and doesn't affect determinism.
    
    Args:
        query: The user's search query
        
    Returns:
        List of top 5 ranked results
    """
    # Stage 1: Normalize query
    pattern = normalize_query(query)
    
    # Stage 2: Generate constraints
    constraints = generate_constraints(pattern)
    
    # Stage 3: Map constraints to indices
    indices = map_constraints_to_indices(constraints)
    
    # Stage 4: Generate candidate sequences
    candidates = generate_sequences(indices, constraints)
    
    # Stage 5: Analyze and filter sequences
    valid = analyze_sequences(candidates, constraints)
    
    # Stage 6: Score and rank sequences
    ranked = score_and_rank(valid, constraints)
    
    # Return top 5 results for API (fewer than CLI for efficiency)
    return ranked[:5]


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
        # Validate query
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Execute cached pipeline
        results = cached_pipeline(request.query)
        
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
        # Catch any unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}"
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
            "pipeline_cache_size": cached_pipeline.cache_info().currsize,
            "pipeline_cache_hits": cached_pipeline.cache_info().hits,
            "pipeline_cache_misses": cached_pipeline.cache_info().misses,
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    print("Starting MNN Knowledge Engine API...")
    print("API will be available at: http://localhost:8000")
    print("Interactive docs at: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
