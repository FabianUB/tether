"""
Health check endpoint.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    """Health check endpoint."""
    llm_service = getattr(request.app.state, "llm_service", None)
    model_loaded = llm_service.is_ready() if llm_service else False

    return HealthResponse(
        status="healthy",
        model_loaded=model_loaded,
        version="0.1.0",
    )
