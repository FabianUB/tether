# Tether TODO

Actionable roadmap with priorities. Check off items as they're completed.

---

## Immediate

### Testing

- [ ] Add unit tests for template frontend (hooks, components)
- [ ] Add unit tests for template backend (routes, services)
- [ ] Add integration tests for CLI (`create-tether-app`)
- [ ] Add E2E tests for template (frontend + backend communication)
- [ ] Set up CI/CD with GitHub Actions

### CLI Improvements

- [ ] Add `--dry-run` flag to preview what would be created
- [ ] Better `--help` output with usage examples
- [ ] Improve error messages with actionable suggestions
- [ ] Add `--verbose` flag for debugging

### Cargo Build Optimizations

- [x] Add `.cargo/config.toml` with dev profile settings
- [ ] Document sccache setup for faster rebuilds
- [ ] Document mold/lld linker setup
- [ ] Optimize Tauri feature flags for dev builds
- [ ] Document incremental build patterns

### Local Model Support

- [ ] Fix local model provider detection (auto-detect GGUF files)
- [x] Add Ollama support as LLM provider
- [ ] Test llama-cpp-python on Windows and Linux
- [ ] Add model validation (check GGUF format, file exists)
- [x] Better error messages when model fails to load

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
- [ ] Add `useStreamingChat` hook
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
- [ ] Per-request model selection
- [ ] Model routing based on task type

### UX Improvements

- [ ] Better model download/management UX
- [ ] Add system tray support (optional)
- [ ] Conversation persistence (localStorage or SQLite)
- [ ] Keyboard shortcuts (Cmd+Enter to send, etc.)
- [ ] Dark mode support in template

### Documentation

- [ ] Add troubleshooting guide
- [ ] Document deployment process in detail
- [ ] Add video tutorials
- [ ] Create documentation site (Docusaurus or Astro)

### Examples

- [ ] Create "Image Captioning" example app
- [ ] Create "Document Q&A" example app
- [ ] Create "Code Assistant" example app
- [ ] Add example with custom UI (not chat-based)

---

## Long-term

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

## Tech Debt

- [ ] Review and reduce bundle size
- [ ] Audit dependencies for security vulnerabilities
- [ ] Improve TypeScript strictness (enable strict mode)
- [ ] Add pre-commit hooks (lint-staged, husky)
- [ ] Improve error boundaries in React
- [ ] Add request retry logic with exponential backoff

---

## Nice to Have (Low Priority)

### Web Deployment Support

- [ ] Make frontend detect Tauri vs browser environment
- [ ] Add env-based API URL fallback (`VITE_API_URL`)
- [ ] Create Dockerfile for backend deployment
- [ ] Add docker-compose template
- [ ] Document web deployment workflow

_Note: Local LLM support doesn't apply to web - users would need API providers._

---

## Won't Do (Explicitly Out of Scope)

These items have been considered and rejected:

- **Cloud hosting service**: Tether is local-first
- **Model training features**: Use dedicated ML frameworks
- **Real-time collaboration**: Single-user desktop focus
- **Browser extension**: Desktop-only
- **Mobile support**: Desktop frameworks don't support mobile
- **Plugin system**: Adds complexity; fork and customize instead

---

## Notes

- Priorities may shift based on community feedback
- Each item should have a corresponding GitHub issue when work begins
- Mark items complete with `[x]` and add date completed
