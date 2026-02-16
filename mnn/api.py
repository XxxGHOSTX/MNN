"""
MNN REST API

FastAPI-based REST API for the MNN deterministic pipeline.
Provides HTTP interface for query processing with JSON responses.

Endpoints:
    POST /query - Process a query and return ranked results

Usage:
    uvicorn mnn.api:app --reload
    
    Or with custom host/port:
    uvicorn mnn.api:app --host 0.0.0.0 --port 8080

Example:
    curl -X POST http://localhost:8000/query \\
         -H "Content-Type: application/json" \\
         -d '{"query": "test query"}'

Author: MNN Engine Contributors
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict

from .pipeline import run_pipeline


# FastAPI app instance
app = FastAPI(
    title="MNN Deterministic Pipeline API",
    description="REST API for deterministic Matrix Neural Network query processing",
    version="1.0.0"
)


# Request/Response models
class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str = Field(..., min_length=1, description="Query string to process")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "test query"
            }
        }


class SequenceResult(BaseModel):
    """Model for individual sequence result."""
    sequence: str = Field(..., description="Generated sequence")
    score: float = Field(..., description="Centering score (0.0 to 1.0)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sequence": "XXXXtestXXXX",
                "score": 0.95
            }
        }


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    query: str = Field(..., description="Original query string")
    normalized_query: str = Field(..., description="Normalized query")
    ranked: List[SequenceResult] = Field(..., description="Ranked results")
    count: int = Field(..., description="Number of results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "test query",
                "normalized_query": "TEST QUERY",
                "ranked": [
                    {"sequence": "XXXXtestXXXX", "score": 0.95},
                    {"sequence": "XXtestXXXXXX", "score": 0.89}
                ],
                "count": 2
            }
        }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "MNN Deterministic Pipeline API",
        "version": "1.0.0",
        "endpoints": {
            "POST /query": "Process a query and return ranked results",
            "GET /health": "Health check endpoint"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest) -> QueryResponse:
    """
    Process a query through the MNN pipeline.
    
    Args:
        request: QueryRequest with query string
        
    Returns:
        QueryResponse with ranked results
        
    Raises:
        HTTPException: 400 if query is invalid or produces no results
        HTTPException: 500 if pipeline encounters an error
    """
    try:
        # Import here to get normalized query for response
        from .query_normalizer import normalize_query
        
        query = request.query
        
        # Get normalized query for response
        try:
            normalized_query = normalize_query(query)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Query normalization failed: {str(e)}"
            )
        
        # Run pipeline (cached)
        try:
            ranked_results = run_pipeline(query)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Pipeline error: {str(e)}"
            )
        
        # Convert to response format
        ranked_sequences = [
            SequenceResult(
                sequence=result['sequence'],
                score=result['score']
            )
            for result in ranked_results
        ]
        
        return QueryResponse(
            query=query,
            normalized_query=normalized_query,
            ranked=ranked_sequences,
            count=len(ranked_sequences)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
