# Tether Constitution

This document defines what Tether is, what it isn't, and the principles that guide its development.

---

## Core Principles

### 1. Frontend devs focus on React
Frontend developers should be able to build AI/ML features using familiar React patterns (hooks, components, TypeScript) without needing to understand Python, Rust, or ML internals.

### 2. ML devs focus on Python
Machine learning developers should be able to write inference code, model pipelines, and API endpoints using standard Python tools (FastAPI, asyncio, type hints) without dealing with frontend or desktop concerns.

### 3. Rust is invisible
The Rust/Tauri layer exists purely for desktop integration (window management, sidecar process handling, native APIs). Developers should never need to modify Rust code unless they're extending Tauri capabilities. It just works.

### 4. Easy distribution
End users should receive a single installer (`.dmg`, `.exe`, `.AppImage`) that works out of the box. No Python installation, no npm, no terminal commands. One-click install, one-click run.

---

## What Tether IS

### A template for AI/ML desktop applications
Tether provides a ready-to-use starting point with a React frontend, FastAPI backend with LLM endpoints, and Tauri for desktop packaging. Clone it, customize it, ship it.

### Code you own completely
Once you clone or scaffold a Tether project, it's **your code**. There are no framework dependencies to update, no breaking changes to worry about. Fork it, modify it, delete what you don't need.

### A best practices starting point
The template demonstrates production patterns:
- Type-safe API communication
- Proper async handling
- Clean separation of concerns
- React hooks for state management
- Python abstract base classes for extensibility

### A bridge between ecosystems
Tether handles the complexity of:
- React (TypeScript) <-> Python (FastAPI) communication
- Desktop packaging with embedded Python runtime
- Dynamic port allocation and process management
- Cross-platform compatibility

---

## What Tether is NOT (Anti-Goals)

### Not a framework you depend on
Unlike frameworks where you import their code, Tether generates code that you own. There's no `import tether` in your project.

### Not a full IDE or development environment
Tether is a template, not an editor. Use your preferred IDE (VS Code, PyCharm, etc.).

### Not a model training framework
Tether is for inference, not training. Use PyTorch, TensorFlow, or MLX for model development. Tether helps you deploy trained models in desktop apps.

### Not a cloud service
Tether is designed for local-first applications. While it supports remote APIs (OpenAI, etc.), the primary use case is running models on the user's machine.

### Not trying to replace Electron for non-ML apps
If your app doesn't need Python or ML capabilities, use Electron, Tauri directly, or a web app. Tether's value proposition is the React-Python-Desktop integration.

### Not a model downloader or hub
Tether doesn't manage model discovery or downloads. Users bring their own GGUF files or API keys. Future versions may add model management UX.

---

## Included FastAPI Endpoints

The template includes ready-to-use API endpoints following best practices:

### Health & Status
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with model status |
| `/models` | GET | List available models |
| `/models/switch` | POST | Switch active model |

### Chat & Inference
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Chat completion with history |

### Request/Response Patterns
- **Pydantic models** for request validation and response typing
- **Async handlers** for non-blocking LLM calls
- **Error handling** with proper HTTP status codes
- **CORS middleware** configured for frontend communication

### Extending the API
Add your own endpoints in `backend/app/routes/`. The template demonstrates:
- How to access the LLM service via `request.app.state`
- Proper typing with `Optional`, `Literal`, etc.
- Field validation with Pydantic `Field()`

---

## Ecosystem Compatibility

Tether aims to integrate with the best existing tools rather than reinventing the wheel:

### Observability
Compatible with OpenTelemetry-based tools like [Arize Phoenix](https://github.com/Arize-ai/phoenix), [Langfuse](https://langfuse.com), and [OpenLLMetry](https://github.com/traceloop/openllmetry).

### Guardrails & Safety
Works with [Guardrails AI](https://github.com/guardrails-ai/guardrails), [NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails), and [Presidio](https://github.com/microsoft/presidio) for input/output validation.

### Frameworks
Supports integration with [LangChain](https://langchain.com), [DSPy](https://github.com/stanfordnlp/dspy), and [LlamaIndex](https://llamaindex.ai).

**You bring your preferred tools. Tether just makes sure they work.**

---

## Technology Decisions

### Why Tauri instead of Electron?
- **Smaller bundle size**: ~10MB vs ~150MB+ for Electron
- **Lower memory footprint**: Uses native webview instead of bundled Chromium
- **Better security model**: Rust's memory safety, permission-based IPC
- **Modern Rust ecosystem**: Active development, good async support

### Why FastAPI instead of Flask/Django?
- **Async-first**: Native async/await, essential for streaming LLM responses
- **Type hints**: Automatic validation and documentation via Pydantic
- **Performance**: ASGI-based, suitable for concurrent ML requests
- **Modern Python**: Embraces Python 3.10+ features

### Why uv instead of pip/poetry?
- **Speed**: 10-100x faster dependency resolution
- **Reliability**: Deterministic lockfiles, better conflict resolution
- **Simplicity**: Single tool for venvs, packages, and Python versions
- **Future-proof**: Rapidly becoming the standard for Python packaging

### Why llama-cpp-python for local LLMs?
- **Cross-platform**: Works on macOS (Metal), Windows (CUDA), Linux
- **GGUF support**: Quantized models from Hugging Face ecosystem
- **Memory efficient**: CPU inference viable, GPU acceleration optional
- **Active community**: Regular updates, good documentation

### Why pnpm?
- **Disk efficient**: Content-addressable storage, symlinked dependencies
- **Strict mode**: Catches phantom dependencies, ensures reproducibility
- **Workspace support**: Monorepo-friendly, good for multi-package projects

---

## Roadmap

This is the high-level vision. For detailed, trackable tasks see [TODO.md](./TODO.md).

### Phase 1: Foundation (Complete)
Core template with React + FastAPI + Tauri, local LLM integration, and OpenAI API support.

### Phase 2: Production Readiness (Current)
Testing, error handling, Ollama support, CLI improvements.

### Phase 3: Streaming Support
Server-Sent Events for token streaming, frontend streaming hooks, and typewriter effects.

### Phase 4: Provider Expansion
Additional providers (Anthropic, Google Gemini) and improved provider abstractions.

### Future
GUI model manager, RAG templates, and developer tooling.

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-01 | Use Tauri 2.x | Stable release, better sidecar support |
| 2025-01 | Use uv for Python | 10x faster than pip, better lockfiles |
| 2025-01 | Abstract LLMService base class | Easy to add new providers |
| 2025-01 | Dynamic port allocation | Avoid conflicts with other apps |
| 2025-01 | No streaming in v0.1 | Simpler to get working first |
| 2026-01 | Template over framework | Users own their code completely |

---

## Contributing Philosophy

1. **Keep it simple**: Resist adding features until there's clear demand
2. **Maintain separation**: Changes to one layer shouldn't require changes to others
3. **Test the boundaries**: Integration tests at API boundaries matter more than unit tests
4. **Document decisions**: When making architectural choices, update this document
5. **Prioritize DX**: If something is confusing for developers, fix the API, not the docs
