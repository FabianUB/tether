"""Tests for Ollama LLM service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestOllamaService:
    """Test OllamaService class."""

    @pytest.fixture
    def mock_httpx_client(self):
        """Create a mock httpx client."""
        client = AsyncMock()
        return client

    def test_import_ollama_service(self):
        """Test that OllamaService can be imported."""
        from tether.llm import get_ollama_service
        OllamaService = get_ollama_service()
        assert OllamaService is not None

    def test_ollama_service_init(self):
        """Test OllamaService initialization."""
        from tether.llm import get_ollama_service
        OllamaService = get_ollama_service()

        service = OllamaService(model="llama3.2", base_url="http://localhost:11434")
        assert service.model_name == "llama3.2"
        assert service._base_url == "http://localhost:11434"
        assert service.service_type == "ollama"

    def test_ollama_service_default_values(self):
        """Test OllamaService default values."""
        from tether.llm import get_ollama_service
        OllamaService = get_ollama_service()

        service = OllamaService()
        assert service.model_name == "llama3.2"
        assert service._base_url == "http://localhost:11434"
        assert service._timeout == 120.0

    @pytest.mark.asyncio
    async def test_ollama_not_ready_before_init(self):
        """Test that service is not ready before initialization."""
        from tether.llm import get_ollama_service
        OllamaService = get_ollama_service()

        service = OllamaService()
        assert not service.is_ready()

    @pytest.mark.asyncio
    async def test_complete_raises_without_init(self):
        """Test that complete raises error without initialization."""
        from tether.llm import get_ollama_service
        OllamaService = get_ollama_service()

        service = OllamaService()
        with pytest.raises(RuntimeError, match="not initialized"):
            await service.complete("test prompt")
