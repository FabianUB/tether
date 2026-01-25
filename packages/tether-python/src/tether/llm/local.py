"""
Local LLM service using llama-cpp-python.
"""

import asyncio
from typing import AsyncIterator, Literal, Optional

try:
    from llama_cpp import Llama
except ImportError:
    raise ImportError(
        "llama-cpp-python not installed. Install with: pip install tether[local]"
    )

from tether.llm.base import LLMService


class LocalLLMService(LLMService):
    """
    LLM service using llama-cpp-python for local model inference.
    """

    service_type: Literal["local", "openai", "custom"] = "local"

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
        verbose: bool = False,
    ):
        """
        Initialize local LLM service.

        Args:
            model_path: Path to the GGUF model file
            n_ctx: Context window size
            n_gpu_layers: Number of layers to offload to GPU (-1 for all)
            verbose: Enable verbose logging
        """
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._n_gpu_layers = n_gpu_layers
        self._verbose = verbose
        self._llm: Optional[Llama] = None
        self._ready = False

    @property
    def model_name(self) -> str:
        return self._model_path.split("/")[-1] if self._model_path else "unknown"

    @property
    def context_length(self) -> int:
        return self._n_ctx

    async def initialize(self) -> None:
        """Load the model."""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model)

    def _load_model(self) -> None:
        """Synchronously load the model."""
        self._llm = Llama(
            model_path=self._model_path,
            n_ctx=self._n_ctx,
            n_gpu_layers=self._n_gpu_layers,
            verbose=self._verbose,
        )
        self._ready = True

    async def cleanup(self) -> None:
        """Cleanup resources."""
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
        """Generate a completion using the local model."""
        if not self._llm:
            raise RuntimeError("Model not loaded")

        # Run inference in thread pool
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

    async def stream(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream a completion using the local model."""
        if not self._llm:
            raise RuntimeError("Model not loaded")

        # For streaming, we use the generator interface
        # Note: This is a simplified implementation
        # In production, you might want to use a proper async queue

        def generate():
            return self._llm(
                prompt,
                max_tokens=max_tokens or 512,
                temperature=temperature,
                echo=False,
                stream=True,
            )

        loop = asyncio.get_event_loop()

        # Create async generator from sync generator
        sync_gen = await loop.run_in_executor(None, generate)

        for chunk in sync_gen:
            if chunk["choices"][0]["text"]:
                yield chunk["choices"][0]["text"]
