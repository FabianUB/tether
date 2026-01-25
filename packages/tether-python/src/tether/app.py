"""
FastAPI app factory for Tether applications.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tether.config import get_settings
from tether.models import HealthResponse, ModelInfo


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    llm_service = getattr(app.state, "llm_service", None)
    if llm_service is not None:
        await llm_service.initialize()

    yield

    # Shutdown
    if llm_service is not None:
        await llm_service.cleanup()


def create_app(
    title: str = "Tether App",
    version: str = "0.1.0",
    llm_service: Optional["LLMService"] = None,
    cors_origins: Optional[list[str]] = None,
) -> FastAPI:
    """
    Create a FastAPI application with Tether defaults.

    Args:
        title: Application title
        version: Application version
        llm_service: Optional LLM service instance
        cors_origins: List of allowed CORS origins (default: ["*"])

    Returns:
        Configured FastAPI application
    """
    settings = get_settings()

    app = FastAPI(
        title=title,
        version=version,
        lifespan=lifespan,
    )

    # Store LLM service in app state
    app.state.llm_service = llm_service

    # Configure CORS
    origins = cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Health check endpoint."""
        model_loaded = False
        if app.state.llm_service is not None:
            model_loaded = app.state.llm_service.is_ready()

        return HealthResponse(
            status="healthy",
            model_loaded=model_loaded,
            version=version,
        )

    # Model info endpoint
    @app.get("/model", response_model=ModelInfo)
    async def model_info() -> ModelInfo:
        """Get model information."""
        if app.state.llm_service is None:
            return ModelInfo(
                name="none",
                loaded=False,
                type="custom",
            )

        return ModelInfo(
            name=app.state.llm_service.model_name,
            loaded=app.state.llm_service.is_ready(),
            type=app.state.llm_service.service_type,
            context_length=getattr(app.state.llm_service, "context_length", None),
        )

    return app


# Import LLMService for type hints (avoid circular import)
from tether.llm.base import LLMService  # noqa: E402
