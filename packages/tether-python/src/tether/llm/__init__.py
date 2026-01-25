"""
LLM service abstractions for Tether.
"""

from tether.llm.base import LLMService

__all__ = ["LLMService"]

# Conditional imports to avoid requiring all backends
def get_openai_service():
    """Get OpenAI service (requires openai extra)."""
    from tether.llm.openai import OpenAIService
    return OpenAIService


def get_local_service():
    """Get local LLM service (requires local extra)."""
    from tether.llm.local import LocalLLMService
    return LocalLLMService


def get_ollama_service():
    """Get Ollama service (requires ollama extra)."""
    from tether.llm.ollama import OllamaService
    return OllamaService


def get_mock_service():
    """Get mock service for testing."""
    from tether.llm.base import MockLLMService
    return MockLLMService
