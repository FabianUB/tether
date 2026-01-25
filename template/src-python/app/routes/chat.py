"""
Chat completion endpoints.
"""

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[int] = None


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message")
    history: Optional[list[ChatMessage]] = Field(
        default=None, description="Previous messages in the conversation"
    )
    model: Optional[str] = Field(default=None, description="Model to use")
    temperature: Optional[float] = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        default=None, ge=1, description="Maximum tokens to generate"
    )


class ChatResponse(BaseModel):
    response: str = Field(..., description="The assistant's response")
    tokens_used: Optional[int] = Field(
        default=None, description="Number of tokens used"
    )
    model: Optional[str] = Field(default=None, description="Model used")
    finish_reason: Optional[Literal["stop", "length", "error"]] = Field(
        default="stop", description="Reason for completion"
    )


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    """Generate a chat completion."""
    llm_service = getattr(request.app.state, "llm_service", None)

    if llm_service is None or not llm_service.is_ready():
        raise HTTPException(status_code=503, detail="LLM service not available")

    try:
        # Build prompt from history if provided
        prompt = body.message
        if body.history:
            history_text = "\n".join(
                f"{msg.role}: {msg.content}" for msg in body.history
            )
            prompt = f"{history_text}\nuser: {body.message}\nassistant:"

        response = await llm_service.complete(
            prompt,
            temperature=body.temperature or 0.7,
            max_tokens=body.max_tokens,
        )

        return ChatResponse(
            response=response,
            model=llm_service.model_name,
            finish_reason="stop",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
