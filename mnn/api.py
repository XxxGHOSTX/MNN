"""
FastAPI web service for MNN engine.

Provides REST API endpoint for query processing.

Usage:
    uvicorn mnn.api:app --reload
    
    Or with custom host/port:
    uvicorn mnn.api:app --host 127.0.0.1 --port 8000

Endpoints:
    POST /query
        Request: {"query": "hello world"}
        Response: {"results": [...], "count": N}
"""

import os
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mnn.pipeline import run_pipeline


# Request/Response models
class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str = Field(..., min_length=1, description="Query string to process")


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    results: List[Dict[str, Any]] = Field(..., description="Ranked results")
    count: int = Field(..., description="Number of results")


# Initialize FastAPI app
app = FastAPI(
    title="MNN Engine API",
    description="Matrix Neural Network deterministic query processing API",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "MNN Engine API",
        "version": "1.0.0",
        "endpoints": {
            "/query": "POST - Process a query through MNN pipeline"
        }
    }


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query through the MNN pipeline.
    
    Args:
        request: QueryRequest with query string.
    
    Returns:
        QueryResponse with ranked results.
    
    Raises:
        HTTPException: If query processing fails.
    
    Examples:
        POST /query
        {
            "query": "hello world"
        }
        
        Response:
        {
            "results": [
                {"sequence": "HELLO WORLDXXX...", "score": 0.95},
                ...
            ],
            "count": 100
        }
    """
    try:
        # Run pipeline
        results = run_pipeline(request.query)
        
        return QueryResponse(
            results=results,
            count=len(results)
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# For running with uvicorn
if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("MNN_API_HOST", "127.0.0.1")
    port = int(os.environ.get("MNN_API_PORT", "8000"))
    
    uvicorn.run(app, host=host, port=port)
