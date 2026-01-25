# Tether TODO

Actionable roadmap with priorities. Check off items as they're completed.

---

## Immediate (Production Readiness)

### Testing
- [ ] Add unit tests for `tether-core` (hooks, api-client, types)
- [ ] Add unit tests for `tether-python` (app factory, LLM services)
- [ ] Add integration tests for CLI (`create-tether-app`)
- [ ] Add E2E tests for template (frontend + backend communication)
- [ ] Set up CI/CD with GitHub Actions

### Local Model Support
- [ ] Fix local model provider detection (auto-detect GGUF files)
- [ ] Add Ollama support as LLM provider
- [ ] Test llama-cpp-python on Windows and Linux
- [ ] Add model validation (check GGUF format, file exists)
- [ ] Better error messages when model fails to load

### Publishing
- [ ] Publish `create-tether-app` to npm
- [ ] Publish `@tether/core` to npm
- [ ] Publish `tether` to PyPI
- [ ] Set up automated release workflow
- [ ] Add changelog automation (conventional commits)

### Polish
- [ ] Add proper error handling with user-friendly messages
- [ ] Generate app icons for template (macOS, Windows, Linux)
- [ ] Add loading states for model initialization
- [ ] Improve CLI output (progress indicators, colors)
- [ ] Add `--verbose` flag to CLI for debugging

---

## Short-term

### Streaming Support
- [ ] Implement SSE endpoint in Python backend
- [ ] Add `useStreamingChat` hook to tether-core
- [ ] Create typewriter effect component
- [ ] Handle backpressure and cancellation
- [ ] Add streaming to OpenAI provider
- [ ] Add streaming to local LLM provider

### Anthropic API Support
- [ ] Create `AnthropicLLMService` class
- [ ] Add Claude model support
- [ ] Handle Anthropic-specific parameters
- [ ] Add to template as provider option

### UX Improvements
- [ ] Better model download/management UX
- [ ] Add system tray support (optional)
- [ ] Conversation persistence (localStorage or SQLite)
- [ ] Keyboard shortcuts (Cmd+Enter to send, etc.)
- [ ] Dark mode support in template

### Documentation
- [ ] Create documentation site (Docusaurus or Astro)
- [ ] Add API reference docs
- [ ] Add video tutorials
- [ ] Add troubleshooting guide
- [ ] Document deployment process in detail

### Examples
- [ ] Create "Image Captioning" example app
- [ ] Create "Document Q&A" example app
- [ ] Create "Code Assistant" example app
- [ ] Add example with custom UI (not chat-based)

---

## Long-term

### Plugin System
- [ ] Design plugin architecture
- [ ] Create provider plugin interface
- [ ] Create UI plugin interface
- [ ] Plugin discovery and loading
- [ ] Plugin marketplace/registry

### GUI Model Manager
- [ ] Model browser (Hugging Face integration)
- [ ] One-click model download
- [ ] Model configuration UI
- [ ] Model deletion and cleanup
- [ ] Download progress tracking

### RAG Template
- [ ] Create RAG-specific template
- [ ] Add local embeddings support (sentence-transformers)
- [ ] Vector store integration (ChromaDB or similar)
- [ ] Document chunking utilities
- [ ] Citation/source tracking

### Developer Experience
- [ ] VS Code extension for debugging
- [ ] DevTools panel in app
- [ ] Hot reload for Python backend
- [ ] Request/response inspector
- [ ] Performance profiling

### Advanced Features
- [ ] Multi-model chat (compare responses side-by-side)
- [ ] Function calling / tool use support
- [ ] Voice input/output integration
- [ ] Image generation support (Stable Diffusion)
- [ ] Fine-tuning workflow integration

---

## Tech Debt

- [ ] Review and reduce bundle size
- [ ] Audit dependencies for security vulnerabilities
- [ ] Improve TypeScript strictness (enable strict mode)
- [ ] Add pre-commit hooks (lint-staged, husky)
- [ ] Improve error boundaries in React
- [ ] Add request retry logic with exponential backoff

---

## Won't Do (Explicitly Out of Scope)

These items have been considered and rejected:

- **Cloud hosting service**: Tether is local-first
- **Model training features**: Use dedicated ML frameworks
- **Real-time collaboration**: Single-user desktop focus
- **Browser extension**: Desktop-only
- **Mobile support**: Desktop frameworks don't support mobile

---

## Notes

- Priorities may shift based on community feedback
- Each item should have a corresponding GitHub issue when work begins
- Mark items complete with `[x]` and add date completed
- Move completed items to a "Done" section periodically
