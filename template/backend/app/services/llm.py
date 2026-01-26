"""
LLM service abstraction.
"""

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_ollama_base_url() -> str:
    """Get Ollama base URL from OLLAMA_HOST env var or default."""
    ollama_host = os.environ.get("OLLAMA_HOST")
    if ollama_host:
        if not ollama_host.startswith("http"):
            ollama_host = f"http://{ollama_host}"
        return ollama_host.rstrip("/")
    return "http://localhost:11434"


@dataclass
class OllamaDiscoveryResult:
    """Result of Ollama discovery."""

    available: bool
    base_url: str
    models: list[str]
    error: Optional[str] = None


class LLMSettings(BaseSettings):
    """LLM configuration from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tether_llm_backend: Literal["local", "ollama", "openai", "mock"] = "ollama"
    tether_model_path: Optional[str] = None
    openai_api_key: Optional[str] = None
    tether_openai_model: str = "gpt-4o-mini"
    tether_context_length: int = 4096
    # Ollama settings - model can be empty to auto-select
    tether_ollama_model: Optional[str] = None
    tether_ollama_base_url: Optional[str] = None  # Uses OLLAMA_HOST or default


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


async def discover_ollama(base_url: Optional[str] = None) -> OllamaDiscoveryResult:
    """Discover Ollama instance and available models."""
    import httpx

    url = base_url or get_ollama_base_url()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/api/tags")
            response.raise_for_status()
            tags = response.json()
            models = [m["name"] for m in tags.get("models", [])]
            return OllamaDiscoveryResult(available=True, base_url=url, models=models)
    except httpx.ConnectError:
        return OllamaDiscoveryResult(
            available=False, base_url=url, models=[],
            error=f"Cannot connect to Ollama at {url}. Make sure Ollama is running (run 'ollama serve' or start the Ollama app).",
        )
    except httpx.TimeoutException:
        return OllamaDiscoveryResult(
            available=False, base_url=url, models=[],
            error=f"Connection to Ollama at {url} timed out. The server may be busy or unresponsive.",
        )
    except httpx.HTTPStatusError as e:
        return OllamaDiscoveryResult(
            available=False, base_url=url, models=[],
            error=f"Ollama returned an error (HTTP {e.response.status_code}). Check if Ollama is working correctly.",
        )
    except Exception as e:
        return OllamaDiscoveryResult(
            available=False, base_url=url, models=[],
            error=f"Unexpected error connecting to Ollama: {str(e)}",
        )


class OllamaService(LLMService):
    """Ollama LLM service."""

    service_type: Literal["local", "ollama", "openai", "mock"] = "ollama"

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        settings = get_settings()
        self._model = model or settings.tether_ollama_model  # Can be None
        base = base_url or settings.tether_ollama_base_url
        self._base_url = (base or get_ollama_base_url()).rstrip("/")
        self._client = None
        self._ready = False
        self._available_models: list[str] = []

    @property
    def model_name(self) -> str:
        return self._model or "not-set"

    @property
    def available_models(self) -> list[str]:
        """List of available models (populated after initialize)."""
        return self._available_models

    async def initialize(self) -> None:
        try:
            import httpx

            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(120.0),
            )

            # Discover available models
            discovery = await discover_ollama(self._base_url)

            if not discovery.available:
                error_msg = discovery.error or f"Cannot connect to Ollama at {self._base_url}"
                raise RuntimeError(error_msg)

            self._available_models = discovery.models

            # Auto-select model if not specified
            if not self._model:
                if self._available_models:
                    self._model = self._available_models[0]
                    print(f"Auto-selected Ollama model: {self._model}")
                else:
                    raise RuntimeError(
                        "No models found in Ollama. Pull a model first with:\n"
                        "  ollama pull llama3.2\n"
                        "Or visit https://ollama.com/library to browse available models."
                    )
            else:
                # Verify model exists
                model_found = any(
                    self._model == m or self._model == m.split(":")[0]
                    for m in self._available_models
                )
                if not model_found:
                    available_str = ", ".join(self._available_models[:5])
                    if len(self._available_models) > 5:
                        available_str += f", ... ({len(self._available_models) - 5} more)"
                    if self._available_models:
                        print(
                            f"Warning: Model '{self._model}' not found locally. "
                            f"Available models: {available_str}. "
                            f"Ollama will try to pull it automatically."
                        )
                    else:
                        print(
                            f"Warning: Model '{self._model}' specified but no models found. "
                            f"Ollama will try to pull it automatically."
                        )

            self._ready = True
        except ImportError:
            raise ImportError(
                "httpx package not installed. Install it with:\n"
                "  pip install httpx\n"
                "Or: uv add httpx"
            )

    async def cleanup(self) -> None:
        if self._client:
            await self._client.aclose()
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready and self._client is not None

    async def list_models(self) -> list[str]:
        """List available Ollama models."""
        if self._available_models:
            return self._available_models
        discovery = await discover_ollama(self._base_url)
        return discovery.models

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

    async def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        think: bool = True,
    ) -> dict:
        """
        Chat completion using Ollama's chat API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            think: Enable thinking mode for reasoning models (default: True)

        Returns:
            Dict with 'content' and optionally 'thinking' keys
        """
        if not self._client:
            raise RuntimeError("Ollama client not initialized")

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "think": think,  # Enable thinking mode
            "options": {"temperature": temperature},
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        response = await self._client.post("/api/chat", json=payload)
        response.raise_for_status()

        data = response.json()
        message = data.get("message", {})

        return {
            "content": message.get("content", ""),
            "thinking": message.get("thinking"),  # None if not a thinking model
        }


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
            raise RuntimeError(
                "No model path specified. Set TETHER_MODEL_PATH environment variable "
                "to the path of your GGUF model file.\n"
                "Example: TETHER_MODEL_PATH=./models/llama-3.2-1b.gguf"
            )

        # Check if file exists
        if not os.path.isfile(self._model_path):
            raise RuntimeError(
                f"Model file not found: {self._model_path}\n"
                "Make sure the path is correct and the file exists.\n"
                "You can download GGUF models from: https://huggingface.co/models?library=gguf"
            )

        # Check file extension
        if not self._model_path.lower().endswith(".gguf"):
            print(
                f"Warning: Model file '{self._model_path}' doesn't have .gguf extension. "
                "Make sure this is a valid GGUF model file."
            )

        try:
            from llama_cpp import Llama

            print(f"Loading model: {self._model_path}...")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)
            print(f"Model loaded successfully: {self.model_name}")
        except ImportError:
            raise ImportError(
                "llama-cpp-python package not installed. Install it with:\n"
                "  pip install llama-cpp-python\n"
                "For GPU support, see: https://github.com/abetlen/llama-cpp-python#installation"
            )

    def _load_model(self) -> None:
        from llama_cpp import Llama

        try:
            self._llm = Llama(
                model_path=self._model_path,
                n_ctx=self._n_ctx,
                n_gpu_layers=self._n_gpu_layers,
                verbose=False,
            )
            self._ready = True
        except Exception as e:
            error_str = str(e).lower()
            if "gguf" in error_str or "magic" in error_str:
                raise RuntimeError(
                    f"Invalid model file format: {self._model_path}\n"
                    "This doesn't appear to be a valid GGUF file. "
                    "Make sure you have a properly formatted GGUF model."
                ) from e
            elif "memory" in error_str or "alloc" in error_str:
                raise RuntimeError(
                    f"Not enough memory to load model: {self._model_path}\n"
                    "Try a smaller/quantized model or close other applications."
                ) from e
            else:
                raise RuntimeError(
                    f"Failed to load model: {self._model_path}\n"
                    f"Error: {str(e)}"
                ) from e

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
