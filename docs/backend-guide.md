# Backend Guide

This guide covers building the Python backend for your Tether application. No Rust or frontend knowledge is required.

## Overview

The backend is a FastAPI application that:
- Provides REST API endpoints for the frontend
- Manages LLM inference (local or API-based)
- Gets bundled as a standalone binary for distribution

## Project Structure

```
src-python/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoint
│   │   └── chat.py          # Chat completion endpoint
│   └── services/
│       ├── __init__.py
│       └── llm.py           # LLM service abstraction
├── scripts/
│   └── build.py             # PyInstaller build script
└── pyproject.toml           # Python dependencies
```

## Development

### Install Dependencies

```bash
cd src-python
uv sync
```

### Run Development Server

```bash
uv run uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### API Documentation

FastAPI automatically generates API docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## LLM Service

The `llm.py` file provides an abstraction for different LLM backends:

```python
from app.services.llm import get_llm_service

# Get the configured service
service = get_llm_service()

# Initialize (load model, etc.)
await service.initialize()

# Generate completion
response = await service.complete(
    "What is the capital of France?",
    temperature=0.7,
    max_tokens=100
)
```

### Available Backends

#### Local LLM (llama-cpp-python)

Runs models locally using llama.cpp:

```env
TETHER_LLM_BACKEND=local
TETHER_MODEL_PATH=./models/mistral-7b-instruct.gguf
TETHER_CONTEXT_LENGTH=4096
```

#### OpenAI API

Uses OpenAI's API:

```env
TETHER_LLM_BACKEND=openai
OPENAI_API_KEY=sk-your-api-key
TETHER_OPENAI_MODEL=gpt-4o-mini
```

#### Mock (for testing)

Returns fixed responses:

```env
TETHER_LLM_BACKEND=mock
```

### Creating a Custom Backend

Implement the `LLMService` interface:

```python
from app.services.llm import LLMService

class MyCustomService(LLMService):
    service_type = "custom"
    model_name = "my-model"

    async def initialize(self) -> None:
        # Load model, connect to API, etc.
        pass

    async def cleanup(self) -> None:
        # Release resources
        pass

    def is_ready(self) -> bool:
        return True

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        # Generate completion
        return "Response"
```

## Adding API Endpoints

### Create a New Route

```python
# app/routes/my_endpoint.py
from fastapi import APIRouter, Request
from pydantic import BaseModel

class MyRequest(BaseModel):
    input: str

class MyResponse(BaseModel):
    output: str

router = APIRouter()

@router.post("/my-endpoint", response_model=MyResponse)
async def my_endpoint(request: Request, body: MyRequest) -> MyResponse:
    # Access LLM service
    llm = request.app.state.llm_service

    # Process request
    result = await llm.complete(body.input)

    return MyResponse(output=result)
```

### Register the Route

```python
# app/main.py
from app.routes import health, chat, my_endpoint

def create_app() -> FastAPI:
    app = FastAPI(...)

    # Include routers
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(my_endpoint.router)  # Add your route

    return app
```

## Configuration

Configuration is managed via environment variables:

```python
# Access in code
import os

model_path = os.getenv("TETHER_MODEL_PATH")
backend = os.getenv("TETHER_LLM_BACKEND", "local")
```

### Available Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `TETHER_HOST` | `127.0.0.1` | Server host |
| `TETHER_PORT` | `8000` | Server port |
| `TETHER_LLM_BACKEND` | `local` | LLM backend (local, openai, mock) |
| `TETHER_MODEL_PATH` | - | Path to local model file |
| `TETHER_CONTEXT_LENGTH` | `4096` | Context window size |
| `TETHER_DEFAULT_TEMPERATURE` | `0.7` | Default sampling temperature |
| `TETHER_DEFAULT_MAX_TOKENS` | `1024` | Default max tokens |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `TETHER_OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |

## Building for Production

### Create Standalone Binary

```bash
cd src-python
uv run python scripts/build.py
```

This creates a binary in `src-tauri/binaries/api-{target}`.

### Binary Naming

Tauri requires binaries to be named with the target triple:
- macOS ARM: `api-aarch64-apple-darwin`
- macOS Intel: `api-x86_64-apple-darwin`
- Windows: `api-x86_64-pc-windows-msvc.exe`
- Linux: `api-x86_64-unknown-linux-gnu`

The build script handles this automatically.

## Testing

### Run Tests

```bash
cd src-python
uv run pytest
```

### Test with httpx

```python
# tests/test_chat.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

## GPU Acceleration

### NVIDIA (CUDA)

Install llama-cpp-python with CUDA support:

```bash
CMAKE_ARGS="-DGGML_CUDA=on" uv pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### Apple Silicon (Metal)

Metal support is enabled by default on Apple Silicon.

### AMD (ROCm)

```bash
CMAKE_ARGS="-DGGML_HIPBLAS=on" uv pip install llama-cpp-python --force-reinstall --no-cache-dir
```

## Best Practices

1. **Use async/await** - FastAPI is async-first, use it
2. **Type everything** - Use Pydantic models for request/response
3. **Handle errors** - Return appropriate HTTP status codes
4. **Log important events** - Use Python's logging module
5. **Keep services stateless** - State belongs in app.state

## Common Issues

### Model loading is slow

- Use smaller models for development
- Enable GPU acceleration
- Reduce context length

### Out of memory

- Use quantized models (Q4_K_M, Q5_K_M)
- Reduce context length
- Use a smaller model

### PyInstaller binary too large

- This is expected (100-200MB+)
- Consider using Nuitka for smaller binaries (future feature)
