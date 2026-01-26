"""
Chat completion endpoints.
"""

import re
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    images: Optional[list[str]] = Field(
        default=None, description="Base64-encoded images for vision models"
    )
    timestamp: Optional[int] = None


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message")
    images: Optional[list[str]] = Field(
        default=None, description="Base64-encoded images for vision models"
    )
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
    think: Optional[bool] = Field(
        default=True, description="Enable thinking mode for reasoning models"
    )


class ChatResponse(BaseModel):
    response: str = Field(..., description="The assistant's response")
    thinking: Optional[str] = Field(
        default=None, description="Model's reasoning/thinking content (for thinking models)"
    )
    tokens_used: Optional[int] = Field(
        default=None, description="Number of tokens used"
    )
    model: Optional[str] = Field(default=None, description="Model used")
    finish_reason: Optional[Literal["stop", "length", "error"]] = Field(
        default="stop", description="Reason for completion"
    )


def parse_thinking_content(text: str) -> tuple[str, Optional[str]]:
    """
    Parse thinking content from model response.

    Thinking models like Qwen3 wrap reasoning in <think>...</think> tags.

    Returns:
        Tuple of (response_without_thinking, thinking_content)
    """
    # Match <think>...</think> tags (case insensitive, multiline)
    think_pattern = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)

    thinking_parts = think_pattern.findall(text)

    if not thinking_parts:
        return text, None

    # Remove thinking tags from response
    response = think_pattern.sub("", text).strip()

    # Combine all thinking parts (in case there are multiple)
    thinking = "\n\n".join(part.strip() for part in thinking_parts)

    return response, thinking


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    """Generate a chat completion."""
    llm_service = getattr(request.app.state, "llm_service", None)

    if llm_service is None or not llm_service.is_ready():
        raise HTTPException(status_code=503, detail="LLM service not available")

    try:
        # Build messages list for chat API
        messages = []
        if body.history:
            for msg in body.history:
                msg_dict = {"role": msg.role, "content": msg.content}
                if msg.images:
                    msg_dict["images"] = msg.images
                messages.append(msg_dict)

        # Add current message with optional images
        current_msg = {"role": "user", "content": body.message}
        if body.images:
            current_msg["images"] = body.images
        messages.append(current_msg)

        # Check if any message has images (vision models don't support thinking)
        has_images = body.images or any(
            msg.images for msg in (body.history or []) if msg.images
        )
        # Disable thinking for vision requests (not supported by Ollama)
        use_thinking = False if has_images else (body.think if body.think is not None else True)

        # Use chat API if available (supports thinking models), fallback to complete
        if hasattr(llm_service, "chat"):
            result = await llm_service.chat(
                messages,
                temperature=body.temperature or 0.7,
                max_tokens=body.max_tokens,
                think=use_thinking,
            )
            # chat() returns dict with 'content' and 'thinking'
            if isinstance(result, dict):
                response = result.get("content", "")
                thinking = result.get("thinking")
            else:
                # Fallback if chat returns string
                response, thinking = parse_thinking_content(result)
        else:
            # Fallback for services without chat method
            prompt = body.message
            if body.history:
                history_text = "\n".join(
                    f"{msg.role}: {msg.content}" for msg in body.history
                )
                prompt = f"{history_text}\nuser: {body.message}\nassistant:"
            raw_response = await llm_service.complete(
                prompt,
                temperature=body.temperature or 0.7,
                max_tokens=body.max_tokens,
            )
            response, thinking = parse_thinking_content(raw_response)

        return ChatResponse(
            response=response,
            thinking=thinking,
            model=llm_service.model_name,
            finish_reason="stop",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
