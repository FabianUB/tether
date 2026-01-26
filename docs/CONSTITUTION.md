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

## AI Observability, Guardrails & Ecosystem

Tether's core mission is simple: **make it easy to build AI/ML desktop apps**. The framework itself stays minimal and unopinionated.

However, we believe building *trustworthy* AI applications matters. Rather than reinventing the wheel, Tether aims to integrate seamlessly with the best existing tools in the ecosystem.

### Observability Tools

We prioritize compatibility with established LLM observability libraries:

| Tool | Type | Why it matters |
|------|------|----------------|
| **[Arize Phoenix](https://github.com/Arize-ai/phoenix)** | Open-source | OpenTelemetry-native, vendor-agnostic tracing and evals |
| **[Langfuse](https://langfuse.com)** | Open-source (MIT) | Tracing, prompt management, cost tracking |
| **[OpenLLMetry](https://github.com/traceloop/openllmetry)** | Open-source (Apache 2.0) | OpenTelemetry instrumentation for LLMs |
| **[Opik](https://github.com/comet-ml/opik)** | Open-source (Apache 2.0) | Tracing and evaluation |
| **[LangSmith](https://smith.langchain.com)** | Proprietary | Deep LangChain integration |
| **[Weights & Biases](https://wandb.ai)** | Proprietary | Experiment tracking and evals |

### Guardrails & Safety

For input/output validation, content safety, and structured outputs:

| Tool | Type | Why it matters |
|------|------|----------------|
| **[Guardrails AI](https://github.com/guardrails-ai/guardrails)** | Open-source | Structured output validation, risk detection, Pydantic integration |
| **[NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails)** | Open-source (NVIDIA) | Programmable conversation flows, content moderation, jailbreak detection |
| **[Presidio](https://github.com/microsoft/presidio)** | Open-source (Microsoft) | PII detection and anonymization |

### Framework Compatibility

Tether aims to work well with popular LLM frameworks, enabling developers to use their preferred tools:

| Framework | Focus | Integration goal |
|-----------|-------|------------------|
| **[LangChain](https://langchain.com)** | Chains, agents, RAG | Use LangChain components within Tether's LLM service layer |
| **[DSPy](https://github.com/stanfordnlp/dspy)** | Programmatic prompting, optimization | Support DSPy modules as LLM backends |
| **[LlamaIndex](https://llamaindex.ai)** | Data indexing, RAG | Integrate retrieval pipelines with Tether apps |

### Design Principles

Rather than building custom solutions, Tether will:

1. **Support OpenTelemetry** — Standard tracing format that works with Phoenix, Langfuse, and others
2. **Expose middleware hooks** — Let observability and guardrail tools instrument the request lifecycle
3. **Propagate context** — Pass correlation IDs and metadata through the stack
4. **Stay out of the way** — A hobby chat app uses none of this; an enterprise app plugs in what it needs

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

### Phase 1: Foundation ✓
Core packages, template with React + FastAPI + Tauri, local LLM integration, and OpenAI API support.

### Phase 2: Production Readiness (Current)
Testing, error handling, Ollama support, and publishing to npm/PyPI.

### Phase 3: Streaming Support
Server-Sent Events for token streaming, frontend streaming hooks, and typewriter effects.

### Phase 4: Provider Expansion
Additional providers (Anthropic, Google Gemini) and a unified provider abstraction layer.

### Future
Plugin system, GUI model manager, RAG templates, and developer tooling.

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
