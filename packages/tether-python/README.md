# tether-python

Python backend utilities for Tether AI/ML desktop applications.

## Installation

```bash
# Basic installation
pip install tether

# With OpenAI support
pip install tether[openai]

# With local LLM support
pip install tether[local]

# With all LLM backends
pip install tether[all]
```

## Quick Start

```python
from tether import create_app
from tether.llm import OpenAIService

# Create a FastAPI app with default configuration
app = create_app()

# Or with custom LLM service
from tether.llm import LocalLLMService

service = LocalLLMService(model_path="path/to/model.gguf")
app = create_app(llm_service=service)
```

## Features

- **FastAPI App Factory**: Pre-configured FastAPI application with CORS, health checks, and error handling
- **LLM Abstractions**: Unified interface for OpenAI API and local models (llama-cpp-python)
- **Configuration Management**: Environment-based configuration with sensible defaults
- **Type Safety**: Full type hints and Pydantic models

## API Reference

### `create_app()`

Creates a FastAPI application with Tether defaults.

```python
from tether import create_app

app = create_app(
    title="My App",
    llm_service=None,  # Optional LLM service
    cors_origins=["*"],
)
```

### LLM Services

```python
from tether.llm import LLMService, OpenAIService, LocalLLMService

# OpenAI
service = OpenAIService(api_key="sk-...", model="gpt-4")

# Local model
service = LocalLLMService(model_path="model.gguf", n_ctx=4096)

# Use the service
response = await service.complete("Hello, world!")
```

## License

MIT License
