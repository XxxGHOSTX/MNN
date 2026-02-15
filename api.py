"""
FastAPI service exposing the deterministic MNN pipeline.
"""

from functools import lru_cache
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from main import run_pipeline
from mnn_pipeline.query_normalizer import normalize_query

app = FastAPI(
    title="Matrix Neural Network API",
    description="Deterministic constraint-driven MNN pipeline.",
    version="0.1.0",
)


class QueryRequest(BaseModel):
    """Request body for the /query endpoint."""

    query: str


@lru_cache(maxsize=256)
def _cached_pipeline(query: str) -> List[str]:
    """
    Cache pipeline results for repeated queries to improve responsiveness.
    """
    return run_pipeline(query)


@app.post("/query")
def run_query(payload: QueryRequest) -> dict:
    """
    Execute the MNN pipeline for the provided query and return top results.
    """
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    ranked_sequences = list(_cached_pipeline(payload.query))[:5]
    return {
        "normalized_query": normalize_query(payload.query),
        "results": ranked_sequences,
    }
