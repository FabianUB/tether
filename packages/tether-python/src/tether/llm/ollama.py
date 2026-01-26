"""
Ollama LLM service.
"""

import json
import os
from dataclasses import dataclass
from typing import AsyncIterator, Literal, Optional

try:
    import httpx
except ImportError:
    raise ImportError(
        "httpx package not installed. Install with: pip install tether[ollama]"
    )

from tether.llm.base import LLMService


@dataclass
class OllamaDiscoveryResult:
    """Result of Ollama discovery."""

    available: bool
    base_url: str
    models: list[str]
    error: Optional[str] = None


def get_ollama_base_url() -> str:
    """
    Get Ollama base URL from environment or default.

    Checks OLLAMA_HOST env var first, then falls back to localhost:11434.
    """
    ollama_host = os.environ.get("OLLAMA_HOST")
    if ollama_host:
        # OLLAMA_HOST can be just host:port or full URL
        if not ollama_host.startswith("http"):
            ollama_host = f"http://{ollama_host}"
        return ollama_host.rstrip("/")
    return "http://localhost:11434"


async def discover_ollama(base_url: Optional[str] = None) -> OllamaDiscoveryResult:
    """
    Discover Ollama instance and available models.

    Args:
        base_url: Optional base URL to check. If not provided,
                  checks OLLAMA_HOST env var, then localhost:11434.

    Returns:
        OllamaDiscoveryResult with availability status and models.
    """
    url = base_url or get_ollama_base_url()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/api/tags")
            response.raise_for_status()

            tags = response.json()
            models = [m["name"] for m in tags.get("models", [])]

            return OllamaDiscoveryResult(
                available=True,
                base_url=url,
                models=models,
            )
    except httpx.ConnectError:
        return OllamaDiscoveryResult(
            available=False,
            base_url=url,
            models=[],
            error=f"Cannot connect to Ollama at {url}. Is it running?",
        )
    except Exception as e:
        return OllamaDiscoveryResult(
            available=False,
            base_url=url,
            models=[],
            error=str(e),
        )


class OllamaService(LLMService):
    """
    LLM service using a local Ollama instance.

    Ollama must be running locally (or at the specified base_url).
    See https://ollama.ai for installation.
    """

    service_type: Literal["local", "openai", "ollama", "custom"] = "ollama"

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        """
        Initialize Ollama service.

        Args:
            model: Model to use. If not specified, will use first available model.
            base_url: Ollama API base URL. If not specified, checks OLLAMA_HOST
                      env var, then falls back to http://localhost:11434.
            timeout: Request timeout in seconds (default: 120)
        """
        self._model = model  # Can be None, will be set during initialize()
        self._base_url = (base_url or get_ollama_base_url()).rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
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
        """Initialize the HTTP client and verify Ollama is running."""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
        )

        # Discover Ollama and available models
        discovery = await discover_ollama(self._base_url)

        if not discovery.available:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Make sure Ollama is running (run 'ollama serve')."
            )

        self._available_models = discovery.models

        # Auto-select model if not specified
        if not self._model:
            if self._available_models:
                self._model = self._available_models[0]
                print(f"Auto-selected model: {self._model}")
            else:
                raise RuntimeError(
                    "No models available in Ollama. "
                    "Pull a model first: ollama pull llama3.2"
                )
        else:
            # Check if the requested model is available
            # Model names can be "llama3.2" or "llama3.2:latest"
            model_found = any(
                self._model == m or self._model == m.split(":")[0]
                for m in self._available_models
            )

            if not model_found:
                if self._available_models:
                    print(
                        f"Warning: Model '{self._model}' not found. "
                        f"Available models: {', '.join(self._available_models)}"
                    )
                else:
                    print(
                        f"Warning: Model '{self._model}' not found and no models available. "
                        "Pull a model: ollama pull llama3.2"
                    )

        self._ready = True

    async def cleanup(self) -> None:
        """Cleanup HTTP client."""
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
        """Generate a completion using Ollama API."""
        if not self._client:
            raise RuntimeError("Ollama client not initialized")

        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()

        data = response.json()
        return data.get("response", "")

    async def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a chat completion using Ollama API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            The assistant's response text
        """
        if not self._client:
            raise RuntimeError("Ollama client not initialized")

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        response = await self._client.post("/api/chat", json=payload)
        response.raise_for_status()

        data = response.json()
        return data.get("message", {}).get("content", "")

    async def stream(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream a completion using Ollama API."""
        if not self._client:
            raise RuntimeError("Ollama client not initialized")

        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        async with self._client.stream("POST", "/api/generate", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        continue

    async def stream_chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """
        Stream a chat completion using Ollama API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Text chunks as they are generated
        """
        if not self._client:
            raise RuntimeError("Ollama client not initialized")

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        async with self._client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def list_models(self) -> list[str]:
        """List available models in Ollama."""
        if not self._client:
            raise RuntimeError("Ollama client not initialized")

        response = await self._client.get("/api/tags")
        response.raise_for_status()

        tags = response.json()
        return [m["name"] for m in tags.get("models", [])]

    async def pull_model(self, model: str) -> AsyncIterator[dict]:
        """
        Pull a model from Ollama registry.

        Args:
            model: Model name to pull

        Yields:
            Progress updates as dicts
        """
        if not self._client:
            raise RuntimeError("Ollama client not initialized")

        async with self._client.stream(
            "POST",
            "/api/pull",
            json={"name": model},
            timeout=httpx.Timeout(600.0),  # 10 min timeout for large models
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
