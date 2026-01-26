# Tether

A ready-to-use template for building AI/ML desktop applications. Includes FastAPI backend with LLM endpoints, React frontend with chat UI, and Tauri for desktop packaging.

## Core Principles

1. **Frontend devs focus on React** - No Rust or Python knowledge required
2. **ML devs focus on Python** - No Rust or frontend knowledge required
3. **Rust is invisible** - Works correctly in the background
4. **Easy distribution** - One-click installers for end users

## Quick Start

```bash
# Create a new Tether app
npx create-tether-app my-app

# Navigate to your app
cd my-app

# Install dependencies
pnpm install

# Start development
pnpm dev
```

## Project Structure

```
tether/
├── packages/
│   ├── create-tether-app/    # CLI scaffolding tool
│   ├── tether-core/          # Shared TypeScript utilities
│   └── tether-python/        # Python package (FastAPI + LLM)
├── template/                  # Project template
├── docs/                      # Documentation
└── examples/                  # Example applications
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Desktop | Tauri 2.x | Lightweight, secure shell |
| Frontend | React 18 + Vite | Fast, modern UI development |
| Backend | FastAPI | Async Python API server |
| ML | llama-cpp-python | Local LLM inference |
| Package Manager | uv | Fast Python dependency management |

## Development

```bash
# Install dependencies
pnpm install

# Build all packages
pnpm build

# Run tests
pnpm test

# Format code
pnpm format
```

## Packages

### create-tether-app

CLI tool for scaffolding new Tether projects.

```bash
npx create-tether-app my-app
```

### tether-core

Shared TypeScript utilities including React hooks and type definitions.

```typescript
import { useModel, useApi } from '@tether/core';
```

### tether-python

Python package with FastAPI app factory and LLM integrations.

```python
from tether import create_app, LLMService
```

## License

MIT License - see [LICENSE](LICENSE) for details.
