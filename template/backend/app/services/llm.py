"""
LLM service abstraction.
"""

import asyncio
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """LLM configuration from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tether_llm_backend: Literal["local", "ollama", "openai", "mock"] = "local"
    tether_model_path: Optional[str] = None
    openai_api_key: Optional[str] = None
    tether_openai_model: str = "gpt-4o-mini"
    tether_context_length: int = 4096
    # Ollama settings
    tether_ollama_model: str = "llama3.2"
    tether_ollama_base_url: str = "http://localhost:11434"


@lru_cache
def get_settings() -> LLMSettings:
    return LLMSettings()


class LLMService(ABC):
    """Abstract base class for LLM services."""

    service_type: Literal["local", "ollama", "openai", "mock"] = "mock"
    model_name: str = "unknown"

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if service is ready."""
        pass

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a completion."""
        pass


class MockLLMService(LLMService):
    """Mock LLM service for testing."""

    service_type: Literal["local", "ollama", "openai", "mock"] = "mock"
    model_name = "mock"

    def __init__(self):
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
        return f"This is a mock response to: {prompt[:50]}..."


class OpenAIService(LLMService):
    """OpenAI API service."""

    service_type: Literal["local", "ollama", "openai", "mock"] = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        settings = get_settings()
        self._api_key = api_key or settings.openai_api_key
        self._model = model or settings.tether_openai_model
        self._client = None
        self._ready = False

    @property
    def model_name(self) -> str:
        return self._model

    async def initialize(self) -> None:
        try:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self._api_key)
            self._ready = True
        except ImportError:
            raise ImportError("openai package not installed")

    async def cleanup(self) -> None:
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
        if not self._client:
            raise RuntimeError("OpenAI client not initialized")

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content or ""


class OllamaService(LLMService):
    """Ollama LLM service."""

    service_type: Literal["local", "ollama", "openai", "mock"] = "ollama"

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        settings = get_settings()
        self._model = model or settings.tether_ollama_model
        self._base_url = (base_url or settings.tether_ollama_base_url).rstrip("/")
        self._client = None
        self._ready = False

    @property
    def model_name(self) -> str:
        return self._model

    async def initialize(self) -> None:
        try:
            import httpx

            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(120.0),
            )
            # Verify Ollama is running
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            self._ready = True
        except ImportError:
            raise ImportError("httpx package not installed")
        except Exception as e:
            raise RuntimeError(f"Cannot connect to Ollama at {self._base_url}: {e}")

    async def cleanup(self) -> None:
        if self._client:
            await self._client.aclose()
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
        if not self._client:
            raise RuntimeError("Ollama client not initialized")

        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        return response.json().get("response", "")


class LocalLLMService(LLMService):
    """Local LLM service using llama-cpp-python."""

    service_type: Literal["local", "ollama", "openai", "mock"] = "local"

    def __init__(
        self,
        model_path: Optional[str] = None,
        n_ctx: Optional[int] = None,
        n_gpu_layers: int = -1,
    ):
        settings = get_settings()
        self._model_path = model_path or settings.tether_model_path
        self._n_ctx = n_ctx or settings.tether_context_length
        self._n_gpu_layers = n_gpu_layers
        self._llm = None
        self._ready = False

    @property
    def model_name(self) -> str:
        if self._model_path:
            return self._model_path.split("/")[-1]
        return "unknown"

    async def initialize(self) -> None:
        if not self._model_path:
            print("Warning: No model path specified. LLM service will not be available.")
            return

        try:
            from llama_cpp import Llama

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)
        except ImportError:
            raise ImportError("llama-cpp-python package not installed")

    def _load_model(self) -> None:
        from llama_cpp import Llama

        self._llm = Llama(
            model_path=self._model_path,
            n_ctx=self._n_ctx,
            n_gpu_layers=self._n_gpu_layers,
            verbose=False,
        )
        self._ready = True

    async def cleanup(self) -> None:
        self._llm = None
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready and self._llm is not None

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        if not self._llm:
            raise RuntimeError("Model not loaded")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._llm(
                prompt,
                max_tokens=max_tokens or 512,
                temperature=temperature,
                echo=False,
            ),
        )

        return result["choices"][0]["text"]


def get_llm_service() -> LLMService:
    """Get the appropriate LLM service based on configuration."""
    settings = get_settings()
    backend = settings.tether_llm_backend

    if backend == "openai":
        return OpenAIService()
    elif backend == "ollama":
        return OllamaService()
    elif backend == "local":
        return LocalLLMService()
    else:
        return MockLLMService()
