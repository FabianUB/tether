"""
Model discovery and switching endpoints.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.llm import discover_gemini_models, discover_ollama, get_ollama_base_url


class ModelsResponse(BaseModel):
    available: bool
    current_model: str | None
    models: list[str]
    backend: str
    error: str | None = None
    needs_api_key: bool = False


class SwitchModelRequest(BaseModel):
    model: str = Field(..., description="Model name to switch to")


class SwitchModelResponse(BaseModel):
    success: bool
    previous_model: str | None
    current_model: str
    message: str


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

    # For Gemini, use discovered models
    if backend == "gemini":
        models = getattr(llm_service, "_available_models", [])
        if not models and llm_service.is_ready():
            # Re-discover if models list is empty but service is ready
            client = getattr(llm_service, "_client", None)
            if client:
                discovery = await discover_gemini_models(client)
                if discovery.available:
                    models = discovery.models
        return ModelsResponse(
            available=llm_service.is_ready() or llm_service.needs_api_key,
            current_model=llm_service.model_name if llm_service.is_ready() else None,
            models=models,
            backend=backend,
            needs_api_key=llm_service.needs_api_key,
        )

    # For other backends, return the configured model
    return ModelsResponse(
        available=llm_service.is_ready(),
        current_model=llm_service.model_name,
        models=[llm_service.model_name] if llm_service.is_ready() else [],
        backend=backend,
        needs_api_key=llm_service.needs_api_key,
    )


@router.post("/models/switch", response_model=SwitchModelResponse)
async def switch_model(request: Request, body: SwitchModelRequest) -> SwitchModelResponse:
    """
    Switch to a different model.

    For Ollama backend, switches to the specified model.
    Other backends may not support runtime model switching.
    """
    llm_service = getattr(request.app.state, "llm_service", None)

    if not llm_service:
        raise HTTPException(status_code=503, detail="No LLM service configured")

    if not llm_service.is_ready():
        raise HTTPException(status_code=503, detail="LLM service not ready")

    backend = llm_service.service_type
    previous_model = llm_service.model_name

    # For Ollama, we can switch models at runtime
    if backend == "ollama":
        # Verify the model exists
        discovery = await discover_ollama(get_ollama_base_url())
        if not discovery.available:
            raise HTTPException(status_code=503, detail="Ollama not available")

        # Check if model is in available models (exact match or base name match)
        model_found = any(
            body.model == m or body.model == m.split(":")[0]
            for m in discovery.models
        )

        if not model_found:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{body.model}' not found. Available: {', '.join(discovery.models)}",
            )

        # Switch the model
        llm_service._model = body.model

        return SwitchModelResponse(
            success=True,
            previous_model=previous_model,
            current_model=body.model,
            message=f"Switched from {previous_model} to {body.model}",
        )

    # For Gemini, switch to the requested model
    if backend == "gemini":
        available = getattr(llm_service, "_available_models", [])
        if body.model not in available:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{body.model}' not found. Available: {', '.join(available)}",
            )

        llm_service._model = body.model

        return SwitchModelResponse(
            success=True,
            previous_model=previous_model,
            current_model=body.model,
            message=f"Switched from {previous_model} to {body.model}",
        )

    # Other backends don't support runtime switching
    raise HTTPException(
        status_code=400,
        detail=f"Backend '{backend}' does not support runtime model switching",
    )
