"""
Ollama LLM service.
"""

import json
from typing import AsyncIterator, Literal, Optional

try:
    import httpx
except ImportError:
    raise ImportError(
        "httpx package not installed. Install with: pip install tether[ollama]"
    )

from tether.llm.base import LLMService


class OllamaService(LLMService):
    """
    LLM service using a local Ollama instance.

    Ollama must be running locally (or at the specified base_url).
    See https://ollama.ai for installation.
    """

    service_type: Literal["local", "openai", "ollama", "custom"] = "ollama"

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ):
        """
        Initialize Ollama service.

        Args:
            model: Model to use (default: llama3.2)
            base_url: Ollama API base URL (default: http://localhost:11434)
            timeout: Request timeout in seconds (default: 120)
        """
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._ready = False

    @property
    def model_name(self) -> str:
        return self._model

    async def initialize(self) -> None:
        """Initialize the HTTP client and verify Ollama is running."""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
        )

        # Verify Ollama is running and model is available
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()

            # Check if the requested model is available
            tags = response.json()
            available_models = [m["name"] for m in tags.get("models", [])]

            # Model names can be "llama3.2" or "llama3.2:latest"
            model_found = any(
                self._model == m or self._model == m.split(":")[0]
                for m in available_models
            )

            if not model_found and available_models:
                print(f"Warning: Model '{self._model}' not found. Available: {available_models}")

            self._ready = True
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Make sure Ollama is running (run 'ollama serve')."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Ollama: {e}")

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
