"""
Base LLM service interface.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Literal, Optional


class LLMService(ABC):
    """
    Abstract base class for LLM services.

    All LLM backends should implement this interface.
    """

    service_type: Literal["local", "openai", "ollama", "custom"] = "custom"
    model_name: str = "unknown"

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the service (load models, etc).
        Called during app startup.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Cleanup resources.
        Called during app shutdown.
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """
        Check if the service is ready to handle requests.
        """
        pass

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a completion for the given prompt.

        Args:
            prompt: The input prompt
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate

        Returns:
            The generated completion text
        """
        pass

    async def stream(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """
        Stream a completion for the given prompt.

        Default implementation falls back to non-streaming complete().
        Override for true streaming support.

        Args:
            prompt: The input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Text chunks as they are generated
        """
        result = await self.complete(
            prompt, temperature=temperature, max_tokens=max_tokens
        )
        yield result


class MockLLMService(LLMService):
    """
    Mock LLM service for testing and development.
    """

    service_type: Literal["local", "openai", "ollama", "custom"] = "custom"
    model_name: str = "mock"

    def __init__(self, response: str = "This is a mock response."):
        self._response = response
        self._ready = False

    async def initialize(self) -> None:
        self._ready = True

    async def cleanup(self) -> None:
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        return self._response
