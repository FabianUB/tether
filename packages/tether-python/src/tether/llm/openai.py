"""
OpenAI API LLM service.
"""

from typing import AsyncIterator, Literal, Optional

try:
    from openai import AsyncOpenAI
except ImportError:
    raise ImportError(
        "OpenAI package not installed. Install with: pip install tether[openai]"
    )

from tether.llm.base import LLMService


class OpenAIService(LLMService):
    """
    LLM service using the OpenAI API.
    """

    service_type: Literal["local", "openai", "custom"] = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
    ):
        """
        Initialize OpenAI service.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4o-mini)
            base_url: Optional custom base URL for API-compatible services
        """
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._client: Optional[AsyncOpenAI] = None
        self._ready = False

    @property
    def model_name(self) -> str:
        return self._model

    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        self._client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )
        self._ready = True

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._client:
            await self._client.close()
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready and self._client is not None

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a completion using OpenAI API."""
        if not self._client:
            raise RuntimeError("OpenAI client not initialized")

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content or ""

    async def stream(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream a completion using OpenAI API."""
        if not self._client:
            raise RuntimeError("OpenAI client not initialized")

        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
