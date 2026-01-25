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

## AI Accountability Principles

Building trustworthy AI applications requires more than just working code. Tether is designed around four guiding principles that help developers build accountable AI:

### Ownership — Who's responsible?
Every AI action should have a clear chain of responsibility.

### Traceability — Where did this come from?
AI responses should be traceable to their source.

### Observability — What's happening inside?
Developers need visibility into AI behavior.

### Verifiability — Does it do what we expect?
AI outputs should be testable and reproducible.

### How Tether Enables These Principles

Tether's core stays minimal. Accountability features are **opt-in through plugins**:

```
@tether/plugin-tracing       # Correlation IDs, request logging
@tether/plugin-metrics       # Token usage, latency, cost tracking
@tether/plugin-audit         # Audit trails, permission logs
tether-plugin-observability  # Python-side metrics and logging
```

The core framework provides:
- **Hook points** — Middleware and events where plugins attach (request lifecycle, LLM calls)
- **Standard interfaces** — Common types for logging, metrics, and tracing
- **Context propagation** — Pass correlation IDs and metadata through the stack

A hobby project uses none of these. An enterprise healthcare app uses all of them. Same framework, different plugins. Developers pay the complexity cost only for features they actually need.

---

## What Tether IS

### A framework for AI/ML desktop applications
Tether provides the plumbing to connect a React frontend to a Python backend running local or remote LLMs, all packaged as a desktop app.

### A scaffolding tool
`create-tether-app` generates a working project structure with sensible defaults, so developers can start building features immediately instead of configuring build systems.

### A best practices template
The generated project demonstrates production patterns:
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

### Not a full IDE or development environment
Tether is a framework, not an editor. Use your preferred IDE (VS Code, PyCharm, etc.).

### Not a model training framework
Tether is for inference, not training. Use PyTorch, TensorFlow, or MLX for model development. Tether helps you deploy trained models in desktop apps.

### Not a cloud service
Tether is designed for local-first applications. While it supports remote APIs (OpenAI, etc.), the primary use case is running models on the user's machine.

### Not trying to replace Electron for non-ML apps
If your app doesn't need Python or ML capabilities, use Electron, Tauri directly, or a web app. Tether's value proposition is the React-Python-Desktop integration.

### Not a model downloader or hub
Tether doesn't manage model discovery or downloads. Users bring their own GGUF files or API keys. Future versions may add model management UX.

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

### Phase 1: Foundation (Complete)
- [x] Core packages (`create-tether-app`, `@tether/core`, `tether`)
- [x] Template with React + FastAPI + Tauri
- [x] Local LLM integration via llama-cpp-python
- [x] OpenAI API support
- [x] Basic documentation

### Phase 2: Production Readiness (Current)
- [ ] Unit and integration tests
- [ ] Fix local model provider detection
- [ ] Add Ollama support
- [ ] Publish to npm and PyPI
- [ ] Generate app icons
- [ ] Comprehensive error handling

### Phase 3: Streaming Support
- [ ] Server-Sent Events (SSE) for token streaming
- [ ] Frontend streaming hook (`useStreamingChat`)
- [ ] Typewriter effect component
- [ ] Backpressure handling

### Phase 4: Provider Expansion
- [ ] Ollama integration (chat, embeddings)
- [ ] Anthropic Claude API
- [ ] Google Gemini API
- [ ] Provider abstraction layer

### Future Possibilities
- [ ] Plugin system for custom providers
- [ ] GUI model manager (download, configure, delete)
- [ ] RAG template with local embeddings
- [ ] VS Code extension for debugging
- [ ] Multi-model chat (compare responses)
- [ ] Conversation persistence (SQLite)

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-01 | Use Tauri 2.x | Stable release, better sidecar support |
| 2025-01 | Use uv for Python | 10x faster than pip, better lockfiles |
| 2025-01 | Monorepo structure | Easier to develop/test packages together |
| 2025-01 | Abstract LLMService base class | Easy to add new providers |
| 2025-01 | Dynamic port allocation | Avoid conflicts with other apps |
| 2025-01 | No streaming in v0.1 | Simpler to get working first |

---

## Contributing Philosophy

1. **Keep it simple**: Resist adding features until there's clear demand
2. **Maintain separation**: Changes to one layer shouldn't require changes to others
3. **Test the boundaries**: Integration tests at API boundaries matter more than unit tests
4. **Document decisions**: When making architectural choices, update this document
5. **Prioritize DX**: If something is confusing for developers, fix the API, not the docs
