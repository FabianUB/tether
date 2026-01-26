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
- [x] Add Ollama support as LLM provider
- [ ] Test llama-cpp-python on Windows and Linux
- [ ] Add model validation (check GGUF format, file exists)
- [x] Better error messages when model fails to load

### Publishing
- [ ] Publish `create-tether-app` to npm
- [ ] Publish `@tether/core` to npm
- [ ] Publish `tether` to PyPI
- [ ] Set up automated release workflow
- [ ] Add changelog automation (conventional commits)

### Polish
- [ ] Add proper error handling with user-friendly messages
- [ ] Generate app icons for template (macOS, Windows, Linux)
- [x] Add loading states for model initialization
- [ ] Improve CLI output (progress indicators, colors)
- [ ] Add `--verbose` flag to CLI for debugging

---

## Short-term

### Multimodal: Image Support
- [x] Add `images` parameter to chat API (base64 encoded)
- [x] Update OllamaService to pass images to API
- [x] Add image upload component (file picker)
- [x] Image preview before sending
- [x] Update TypeScript types for image messages
- [x] Auto-disable thinking mode for vision requests
- [x] Warning when using images with thinking enabled
- [ ] Test with LLaVA and Llama 3.2 Vision models
- [x] Drag-drop and paste image support

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

### Model Workflows
- [x] Add model switching endpoint (`POST /models/switch`)
- [x] Add model selector dropdown in frontend
- [ ] Multi-model pool (keep multiple models loaded)
- [ ] Per-request model selection (use `model` field in chat requests)
- [ ] Model routing based on task type
- [ ] Model presets/profiles

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

### ML Endpoint Templates (CLI Selection)
- [ ] Add endpoint selection to CLI (`create-tether-app`)
- [ ] Image Classification template (PyTorch/TensorFlow)
- [ ] Object Detection template (YOLO/ultralytics)
- [ ] Tabular/Predictions template (scikit-learn)
- [ ] Text Classification template (transformers)
- [ ] Embeddings endpoint template (sentence-transformers)

### Examples
- [ ] Create "Image Captioning" example app
- [ ] Create "Document Q&A" example app
- [ ] Create "Code Assistant" example app
- [ ] Add example with custom UI (not chat-based)

---

## Long-term

### Plugin System
See "Plugin System & Accountability" section above for detailed plugin roadmap.
- [ ] Plugin marketplace/registry
- [ ] Community plugin showcase
- [ ] Plugin template for contributors

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

### Multimodal: Audio & Video
- [ ] Audio input with Whisper transcription
- [ ] Voice output (text-to-speech)
- [ ] Real-time audio streaming
- [ ] Video frame extraction for vision models
- [ ] Screen sharing / screenshot input

### Advanced Features
- [ ] Multi-model chat (compare responses side-by-side)
- [ ] Function calling / tool use support
- [ ] Image generation support (Stable Diffusion)
- [ ] Fine-tuning workflow integration

---

## Plugin System & Accountability

Accountability features are opt-in via plugins. Build the plugin infrastructure first, then create first-party plugins.

### Plugin Infrastructure (Core)
- [ ] Design plugin architecture and lifecycle hooks
- [ ] Add middleware system for request/response interception
- [ ] Create standard interfaces for logging, metrics, tracing
- [ ] Implement context propagation (correlation IDs, metadata)
- [ ] Add plugin discovery and loading mechanism
- [ ] Document plugin development guide

### First-Party Plugins

**@tether/plugin-tracing** (Traceability)
- [ ] Correlation IDs for request/response pairs
- [ ] Model identifier in every response
- [ ] Prompt history storage
- [ ] Source attribution for RAG context

**@tether/plugin-metrics** (Observability)
- [ ] Token usage tracking
- [ ] Latency monitoring
- [ ] Cost tracking per provider
- [ ] Dashboard component for metrics

**@tether/plugin-audit** (Ownership)
- [ ] Audit trail logging
- [ ] Permission scopes for LLM actions
- [ ] User/session attribution
- [ ] Responsibility chain documentation

**@tether/plugin-testing** (Verifiability)
- [ ] Mock LLM service for deterministic tests
- [ ] Snapshot testing for prompts
- [ ] Output validation hooks
- [ ] Regression testing utilities

---

## Tech Debt

- [ ] Review and reduce bundle size
- [ ] Audit dependencies for security vulnerabilities
- [ ] Improve TypeScript strictness (enable strict mode)
- [ ] Add pre-commit hooks (lint-staged, husky)
- [ ] Improve error boundaries in React
- [ ] Add request retry logic with exponential backoff

---

## Nice to Have (Low Priority)

Features that would be valuable but aren't essential to the core mission.

### Web Deployment Support
- [ ] Make frontend detect Tauri vs browser environment
- [ ] Add env-based API URL fallback (`VITE_API_URL`)
- [ ] Create Dockerfile for backend deployment
- [ ] Add docker-compose template
- [ ] Document web deployment workflow
- [ ] Consider `--target web` CLI flag for web-only scaffold

*Note: Local LLM support doesn't apply to web — users would need API providers.*

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
