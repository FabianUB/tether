# Tether

A ready-to-use template for building AI/ML desktop applications.

**Stack:** React + Python (FastAPI) + Tauri

## Core Principles

1. **Frontend devs focus on React** - No Rust or Python knowledge required
2. **ML devs focus on Python** - No Rust or frontend knowledge required
3. **Rust is invisible** - Works correctly in the background
4. **Easy distribution** - One-click installers for end users

## Quick Start

```bash
npx create-tether-app my-app
cd my-app
pnpm dev
```

Run `npx create-tether-app --help` for options (LLM backend, Tailwind, etc.).

## Project Structure

```
my-app/
├── frontend/          # React 18 + TypeScript + Vite
├── backend/           # Python 3.11+ + FastAPI + uvicorn
└── src-tauri/         # Tauri 2.x (Rust shell)
```

## Technology Stack

| Layer           | Technology                | Purpose                           |
| --------------- | ------------------------- | --------------------------------- |
| Desktop         | Tauri 2.x                 | Lightweight, secure shell         |
| Frontend        | React 18 + Vite           | Fast, modern UI development       |
| Backend         | FastAPI                   | Async Python API server           |
| ML              | Ollama / llama-cpp-python | Local LLM inference               |
| Package Manager | uv                        | Fast Python dependency management |

## Documentation

- [Getting Started](docs/getting-started.md) - First steps
- [Frontend Guide](docs/frontend-guide.md) - React/TypeScript development
- [Backend Guide](docs/backend-guide.md) - Python/FastAPI development
- [Deployment](docs/deployment.md) - Building installers
- [Development](docs/development.md) - Build optimization tips

## What's Included

- Chat UI component with message history
- LLM service abstraction (Ollama, OpenAI, local models)
- Health check and model switching endpoints
- Image/vision support for multimodal models
- Thinking mode for reasoning models
- Automatic port allocation and process management

## License

MIT License - see [LICENSE](LICENSE) for details.
