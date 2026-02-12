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

    tether_llm_backend: Literal["local", "ollama", "openai", "gemini", "mock"] = "ollama"
    tether_model_path: Optional[str] = None
    openai_api_key: Optional[str] = None
    tether_openai_model: str = "gpt-4o-mini"
    tether_context_length: int = 4096
    # Ollama settings - model can be empty to auto-select
    tether_ollama_model: Optional[str] = None
    tether_ollama_base_url: Optional[str] = None  # Uses OLLAMA_HOST or default
    # Gemini settings
    gemini_api_key: Optional[str] = None
    tether_gemini_model: str = "gemini-2.0-flash"


@lru_cache
def get_settings() -> LLMSettings:
    return LLMSettings()


class LLMService(ABC):
    """Abstract base class for LLM services."""

    service_type: Literal["local", "ollama", "openai", "gemini", "mock"] = "mock"
    model_name: str = "unknown"

    @property
    def needs_api_key(self) -> bool:
        """Whether the service is waiting for an API key."""
        return False

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

    service_type: Literal["local", "ollama", "openai", "gemini", "mock"] = "mock"
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

    service_type: Literal["local", "ollama", "openai", "gemini", "mock"] = "openai"

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
        self._needs_key = False

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def needs_api_key(self) -> bool:
        return self._needs_key

    async def initialize(self) -> None:
        if not self._api_key:
            self._needs_key = True
            return
        self._needs_key = False
        try:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self._api_key)
            self._ready = True
        except ImportError:
            raise ImportError("openai package not installed")

    async def set_api_key(self, api_key: str) -> None:
        """Set the API key at runtime and reinitialize."""
        self._api_key = api_key
        await self.initialize()

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

    async def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        think: bool = True,
    ) -> dict:
        """
        Chat completion using the OpenAI API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            think: Unused (kept for interface consistency)

        Returns:
            Dict with 'content', 'thinking', 'input_tokens', 'output_tokens'
        """
        if not self._client:
            raise RuntimeError("OpenAI client not initialized")

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        usage = response.usage
        return {
            "content": response.choices[0].message.content or "",
            "thinking": None,
            "input_tokens": usage.prompt_tokens if usage else None,
            "output_tokens": usage.completion_tokens if usage else None,
        }


class GeminiService(LLMService):
    """Google Gemini API service."""

    service_type: Literal["local", "ollama", "openai", "gemini", "mock"] = "gemini"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        settings = get_settings()
        self._api_key = api_key or settings.gemini_api_key
        self._model = model or settings.tether_gemini_model
        self._client = None
        self._ready = False
        self._needs_key = False
        self._available_models: list[str] = []

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def needs_api_key(self) -> bool:
        return self._needs_key

    @property
    def available_models(self) -> list[str]:
        """List of available models (populated after initialize)."""
        return self._available_models

    async def initialize(self) -> None:
        if not self._api_key:
            self._needs_key = True
            return
        self._needs_key = False
        try:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)

            # Discover available models
            discovery = await discover_gemini_models(self._client)
            if discovery.available:
                self._available_models = discovery.models
            else:
                print(f"Warning: Could not discover Gemini models: {discovery.error}")
                # Fall back to just the configured model
                self._available_models = [self._model]

            # Verify configured model is available
            if self._available_models and self._model not in self._available_models:
                available_str = ", ".join(self._available_models[:5])
                if len(self._available_models) > 5:
                    available_str += f", ... ({len(self._available_models) - 5} more)"
                print(
                    f"Warning: Model '{self._model}' not found in available models. "
                    f"Available: {available_str}. "
                    f"It may still work if you have access."
                )

            self._ready = True
        except ImportError:
            raise ImportError(
                "google-genai package not installed. Install it with:\n"
                "  pip install google-genai\n"
                "Or: uv add google-genai"
            )

    async def set_api_key(self, api_key: str) -> None:
        """Set the API key at runtime and reinitialize."""
        self._api_key = api_key
        await self.initialize()

    async def cleanup(self) -> None:
        self._client = None
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
            raise RuntimeError("Gemini client not initialized")

        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=config,
        )

        return response.text or ""

    async def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        think: bool = True,
    ) -> dict:
        """
        Chat completion using the Gemini API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            think: Enable thinking for supported models (default: True)

        Returns:
            Dict with 'content' and optionally 'thinking' keys
        """
        if not self._client:
            raise RuntimeError("Gemini client not initialized")

        from google.genai import types

        # Extract system instruction from messages
        system_instruction = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                chat_messages.append(msg)

        # Build history (all messages except the last one)
        history = []
        for msg in chat_messages[:-1]:
            role = "model" if msg["role"] == "assistant" else msg["role"]
            history.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )

        # Build config
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )

        # Enable thinking for 2.5 models
        is_thinking_model = "2.5" in self._model
        if think and is_thinking_model:
            config.thinking_config = types.ThinkingConfig(
                thinking_budget=8192,
            )

        # Create chat and send current message
        chat_session = self._client.aio.chats.create(
            model=self._model,
            history=history,
            config=config,
        )

        current_message = chat_messages[-1]["content"] if chat_messages else ""
        response = await chat_session.send_message(current_message)

        # Parse response parts for thinking content
        thinking_text = None
        content_text = ""

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "thought") and part.thought:
                    thinking_text = (thinking_text or "") + (part.text or "")
                else:
                    content_text += part.text or ""
        else:
            content_text = response.text or ""

        usage = response.usage_metadata
        return {
            "content": content_text,
            "thinking": thinking_text,
            "input_tokens": usage.prompt_token_count if usage else None,
            "output_tokens": usage.candidates_token_count if usage else None,
        }


@dataclass
class GeminiDiscoveryResult:
    """Result of Gemini model discovery."""

    available: bool
    models: list[str]
    error: Optional[str] = None


async def discover_gemini_models(client) -> GeminiDiscoveryResult:
    """Discover available Gemini models from the API."""
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, client.models.list)
        models = []
        for model in response:
            # Only include models that support generateContent
            actions = getattr(model, "supported_actions", None)
            if actions and "generateContent" in actions:
                name = model.name or ""
                # Strip "models/" prefix
                short_name = name.removeprefix("models/")
                if short_name:
                    models.append(short_name)
        models.sort()
        return GeminiDiscoveryResult(available=True, models=models)
    except Exception as e:
        return GeminiDiscoveryResult(
            available=False,
            models=[],
            error=f"Failed to list Gemini models: {str(e)}",
        )


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

    service_type: Literal["local", "ollama", "openai", "gemini", "mock"] = "ollama"

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
            "options": {"temperature": temperature},
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        # Only include think parameter if enabled
        # Some models don't support thinking and will error if it's sent
        if think:
            payload["think"] = True

        response = await self._client.post("/api/chat", json=payload)

        # If request fails and thinking was enabled, retry without it
        # Some models don't support thinking mode and return 400
        if not response.is_success and think:
            payload.pop("think", None)
            response = await self._client.post("/api/chat", json=payload)

        response.raise_for_status()

        data = response.json()
        message = data.get("message", {})

        return {
            "content": message.get("content", ""),
            "thinking": message.get("thinking"),  # None if not a thinking model
            "input_tokens": data.get("prompt_eval_count"),
            "output_tokens": data.get("eval_count"),
        }


class LocalLLMService(LLMService):
    """Local LLM service using llama-cpp-python."""

    service_type: Literal["local", "ollama", "openai", "gemini", "mock"] = "local"

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
    elif backend == "gemini":
        return GeminiService()
    elif backend == "ollama":
        return OllamaService()
    elif backend == "local":
        return LocalLLMService()
    else:
        return MockLLMService()
