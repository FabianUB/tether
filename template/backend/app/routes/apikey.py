"""
API key submission endpoint.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel


class SetApiKeyRequest(BaseModel):
    api_key: str


class SetApiKeyResponse(BaseModel):
    success: bool
    message: str


router = APIRouter()


@router.post("/api-key", response_model=SetApiKeyResponse)
async def set_api_key(request: Request, body: SetApiKeyRequest) -> SetApiKeyResponse:
    """
    Set the API key for the current LLM service at runtime.

    Only supported for backends that require an API key (OpenAI, Gemini).
    The key is stored in memory only and not persisted to disk.
    """
    llm_service = getattr(request.app.state, "llm_service", None)

    if not llm_service:
        raise HTTPException(status_code=503, detail="No LLM service configured")

    if not hasattr(llm_service, "set_api_key"):
        raise HTTPException(
            status_code=400,
            detail=f"Backend '{llm_service.service_type}' does not support runtime API key configuration",
        )

    try:
        await llm_service.set_api_key(body.api_key)
    except Exception as e:
        return SetApiKeyResponse(
            success=False,
            message=f"Failed to initialize with provided key: {str(e)}",
        )

    if llm_service.is_ready():
        return SetApiKeyResponse(
            success=True,
            message="API key accepted. Service is ready.",
        )

    return SetApiKeyResponse(
        success=False,
        message="API key set but service failed to become ready.",
    )
