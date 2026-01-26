"""
Model discovery endpoints.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.llm import discover_ollama, get_ollama_base_url


class ModelsResponse(BaseModel):
    available: bool
    current_model: str | None
    models: list[str]
    backend: str
    error: str | None = None


router = APIRouter()


@router.get("/models", response_model=ModelsResponse)
async def list_models(request: Request) -> ModelsResponse:
    """
    List available models.

    For Ollama backend, discovers available models from the Ollama API.
    For other backends, returns the configured model.
    """
    llm_service = getattr(request.app.state, "llm_service", None)

    if not llm_service:
        return ModelsResponse(
            available=False,
            current_model=None,
            models=[],
            backend="none",
            error="No LLM service configured",
        )

    backend = llm_service.service_type

    # For Ollama, use discovery
    if backend == "ollama":
        discovery = await discover_ollama(get_ollama_base_url())
        return ModelsResponse(
            available=discovery.available,
            current_model=llm_service.model_name if llm_service.is_ready() else None,
            models=discovery.models,
            backend=backend,
            error=discovery.error,
        )

    # For other backends, return the configured model
    return ModelsResponse(
        available=llm_service.is_ready(),
        current_model=llm_service.model_name,
        models=[llm_service.model_name] if llm_service.is_ready() else [],
        backend=backend,
    )
