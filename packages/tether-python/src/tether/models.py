"""
Pydantic models for Tether API.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[int] = None


class ChatRequest(BaseModel):
    """Chat completion request."""

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
    """Chat completion response."""

    response: str = Field(..., description="The assistant's response")
    tokens_used: Optional[int] = Field(
        default=None, description="Number of tokens used"
    )
    model: Optional[str] = Field(default=None, description="Model used")
    finish_reason: Optional[Literal["stop", "length", "error"]] = Field(
        default="stop", description="Reason for completion"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "unhealthy"]
    model_loaded: bool
    version: str
    uptime_seconds: Optional[float] = None


class ModelInfo(BaseModel):
    """Model information."""

    name: str
    loaded: bool
    type: Literal["local", "openai", "custom"]
    context_length: Optional[int] = None


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None
    status_code: int
