"""Tests for Ollama LLM service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestOllamaDiscovery:
    """Test Ollama discovery utilities."""

    def test_get_ollama_base_url_default(self):
        """Test default base URL."""
        from tether.llm.ollama import get_ollama_base_url
        import os

        # Clear env var if set
        env_backup = os.environ.pop("OLLAMA_HOST", None)
        try:
            assert get_ollama_base_url() == "http://localhost:11434"
        finally:
            if env_backup:
                os.environ["OLLAMA_HOST"] = env_backup

    def test_get_ollama_base_url_from_env(self):
        """Test base URL from OLLAMA_HOST env var."""
        from tether.llm.ollama import get_ollama_base_url
        import os

        env_backup = os.environ.get("OLLAMA_HOST")
        try:
            os.environ["OLLAMA_HOST"] = "192.168.1.100:11434"
            assert get_ollama_base_url() == "http://192.168.1.100:11434"

            os.environ["OLLAMA_HOST"] = "http://custom-host:8080"
            assert get_ollama_base_url() == "http://custom-host:8080"
        finally:
            if env_backup:
                os.environ["OLLAMA_HOST"] = env_backup
            else:
                os.environ.pop("OLLAMA_HOST", None)

    def test_discovery_result_dataclass(self):
        """Test OllamaDiscoveryResult dataclass."""
        from tether.llm.ollama import OllamaDiscoveryResult

        result = OllamaDiscoveryResult(
            available=True,
            base_url="http://localhost:11434",
            models=["llama3.2", "gemma3:4b"],
        )
        assert result.available is True
        assert result.models == ["llama3.2", "gemma3:4b"]
        assert result.error is None


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
        # Model is None by default (auto-select on initialize)
        assert service.model_name == "not-set"
        assert service._base_url == "http://localhost:11434"
        assert service._timeout == 120.0

    def test_ollama_service_with_explicit_model(self):
        """Test OllamaService with explicit model."""
        from tether.llm import get_ollama_service
        OllamaService = get_ollama_service()

        service = OllamaService(model="gemma3:4b")
        assert service.model_name == "gemma3:4b"

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
