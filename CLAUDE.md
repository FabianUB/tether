# Claude Guidelines for Tether

Guidelines for Claude (and contributors) when working on the Tether codebase.

---

## Project Overview

Tether is a framework for building AI/ML desktop applications using:
- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: Python 3.11+ + FastAPI + uvicorn
- **Desktop**: Tauri 2.x (Rust)
- **Package Manager**: pnpm (Node), uv (Python)

The codebase is a monorepo managed by Turborepo with three main packages:
- `create-tether-app`: CLI scaffolding tool
- `tether-core`: Shared TypeScript utilities (hooks, types, API client)
- `tether-python`: Python package (FastAPI app factory, LLM services)

---

## Directory Structure

```
tether/
├── packages/
│   ├── create-tether-app/     # CLI tool
│   │   └── src/
│   │       ├── cli.ts         # Commander setup
│   │       ├── prompts.ts     # Inquirer prompts
│   │       ├── scaffold.ts    # File generation
│   │       └── utils.ts       # Helpers
│   │
│   ├── tether-core/           # TypeScript library
│   │   └── src/
│   │       ├── index.ts       # Re-exports
│   │       ├── types.ts       # Type definitions
│   │       ├── config.ts      # Configuration
│   │       ├── api-client.ts  # Fetch wrappers
│   │       └── hooks.ts       # React hooks
│   │
│   └── tether-python/         # Python package
│       └── src/tether/
│           ├── __init__.py    # Package exports
│           ├── app.py         # FastAPI factory
│           ├── config.py      # Settings
│           ├── models.py      # Pydantic models
│           └── llm/
│               ├── base.py    # Abstract LLMService
│               ├── local.py   # llama-cpp-python
│               └── openai.py  # OpenAI API
│
├── template/                   # Scaffolded project template
│   ├── frontend/              # React frontend
│   ├── backend/               # Python backend
│   └── src-tauri/             # Rust/Tauri shell
│
├── docs/                       # Documentation
└── examples/                   # Example applications
```

---

## Code Style & Conventions

### TypeScript

**Naming:**
- `PascalCase` for types, interfaces, classes, React components
- `camelCase` for variables, functions, hooks
- Prefix hooks with `use` (e.g., `useBackendStatus`, `useChat`)
- Prefix interfaces with their purpose, not `I` (e.g., `ChatMessage`, not `IChatMessage`)

**File organization:**
- One primary export per file (types can have multiple)
- Use `index.ts` for re-exports only
- Use `.js` extension in imports (ES modules compatibility)

**Imports:**
```typescript
// External libraries first
import { useState, useCallback } from 'react';

// Internal modules
import { checkHealth } from './api-client.js';
import type { ChatMessage, HealthResponse } from './types.js';
```

**Patterns:**
```typescript
// Use explicit return types on exported functions
export function useChat(): UseChatReturn {
  // ...
}

// Use `type` for type aliases, `interface` for object shapes
type ConnectionStatus = 'connecting' | 'connected' | 'error';

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

// Prefer async/await over .then()
const response = await fetch(url);

// Use optional chaining and nullish coalescing
const name = user?.profile?.name ?? 'Anonymous';
```

### Python

**Follow PEP 8 with these specifics:**
- Line length: 88 characters (Black default)
- Use double quotes for strings
- Use trailing commas in multi-line structures

**Type hints are required:**
```python
from typing import Optional, Literal, AsyncIterator

async def complete(
    self,
    prompt: str,
    *,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> str:
    """Generate a completion."""
    ...
```

**Async patterns:**
```python
# Use async context managers for lifespan
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await startup()
    yield
    await shutdown()

# Run blocking code in executor
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, blocking_function)
```

**Docstrings:**
```python
def create_app(
    title: str = "Tether App",
    llm_service: Optional[LLMService] = None,
) -> FastAPI:
    """
    Create a FastAPI application with Tether defaults.

    Args:
        title: Application title
        llm_service: Optional LLM service instance

    Returns:
        Configured FastAPI application
    """
```

**Imports:**
```python
# Standard library
import asyncio
from typing import Optional

# Third-party
from fastapi import FastAPI
from pydantic import BaseModel

# Local
from tether.config import get_settings
from tether.llm.base import LLMService
```

### Rust

**The Rust code is intentionally minimal.** Only modify when:
- Adding new Tauri commands (IPC endpoints)
- Changing sidecar process management
- Adding native platform features

**Patterns:**
```rust
// Use async_runtime for async operations
tauri::async_runtime::spawn(async move {
    // ...
});

// Proper error handling with Result
pub async fn start(&mut self, app: &AppHandle) -> Result<String, String> {
    // Convert errors to strings for IPC
    command.spawn().map_err(|e| format!("Failed: {}", e))?;
}

// Use Arc<Mutex<T>> for shared state
let manager = Arc::new(Mutex::new(SidecarManager::new(port)));
app.manage(manager);
```

---

## Key Architectural Decisions

### Frontend-Backend Communication
- Frontend uses `fetch()` to call backend API (no Tauri IPC for data)
- Port is obtained via Tauri command `get_api_port()`
- Backend URL is constructed as `http://127.0.0.1:{port}`
- This allows easy testing of backend independently

### LLM Service Abstraction
All LLM backends implement the `LLMService` abstract base class:
```python
class LLMService(ABC):
    @abstractmethod
    async def initialize(self) -> None: ...
    @abstractmethod
    async def cleanup(self) -> None: ...
    @abstractmethod
    def is_ready(self) -> bool: ...
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str: ...
```

### State Management
- Frontend: React hooks (`useState`, `useCallback`) - no Redux/Zustand
- Backend: FastAPI `app.state` for services, Pydantic for data validation
- Cross-cutting: API responses define the contract

### Process Lifecycle
1. Tauri starts, finds available port via `portpicker`
2. Rust spawns Python sidecar with `--port` argument
3. Frontend waits for backend health check to pass
4. On window close, Rust sends SIGTERM to sidecar

---

## How to Add New Features

### Adding a new LLM provider
1. Create `packages/tether-python/src/tether/llm/newprovider.py`
2. Implement `LLMService` interface
3. Add to `packages/tether-python/src/tether/llm/__init__.py`
4. Update type definitions if needed

### Adding a new React hook
1. Add to `packages/tether-core/src/hooks.ts`
2. Export from `packages/tether-core/src/index.ts`
3. Add TypeScript types to `types.ts` if needed

### Adding a new API endpoint
1. Add route in `template/backend/app/routes/`
2. Add Pydantic models in `packages/tether-python/src/tether/models.py`
3. Add corresponding TypeScript types in `packages/tether-core/src/types.ts`
4. Add fetch wrapper in `packages/tether-core/src/api-client.ts`

### Adding a new CLI option
1. Modify `packages/create-tether-app/src/cli.ts` (Commander)
2. Update prompts in `prompts.ts` if interactive
3. Handle in `scaffold.ts` for file generation

---

## Testing Guidelines

### TypeScript (Vitest)
```typescript
import { describe, it, expect, vi } from 'vitest';

describe('useChat', () => {
  it('should add user message to history', async () => {
    // Test implementation
  });
});
```

### Python (pytest)
```python
import pytest
from tether import create_app

@pytest.fixture
def app():
    return create_app()

@pytest.mark.asyncio
async def test_health_endpoint(app):
    # Test implementation
```

### Integration Tests
- Test the full flow: Frontend -> API -> LLM Service
- Use `MockLLMService` for deterministic responses
- Test error cases (backend down, model not loaded)

---

## Common Pitfalls to Avoid

### TypeScript
- **Don't forget `.js` in imports** - ESM requires file extensions
- **Don't use `any`** - Create proper types
- **Don't mutate state directly** - Use `setState` with new objects

### Python
- **Don't block the event loop** - Use `run_in_executor` for sync code
- **Don't forget `await`** - Async functions need await
- **Don't use `from x import *`** - Explicit imports only

### Rust
- **Don't modify unless necessary** - The Rust layer should be stable
- **Don't panic in commands** - Return `Result<T, String>`

### General
- **Don't add dependencies lightly** - Each dep is a maintenance burden
- **Don't break the API contract** - Frontend and backend must agree
- **Don't commit `.env` files** - Use `.env.example` templates

---

## Version Control

### Branching Strategy (GitHub Flow)

We use GitHub Flow: `main` is always deployable, all work happens in feature branches.

```
main (protected)
  │
  ├── feature/streaming-support
  ├── feature/ollama-provider
  ├── fix/windows-path-issue
  └── chore/update-dependencies
```

### Branch Naming

Use prefixes to categorize branches:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feature/` | New functionality | `feature/anthropic-provider` |
| `fix/` | Bug fixes | `fix/sidecar-crash-on-close` |
| `chore/` | Maintenance, CI, docs | `chore/update-ci-workflow` |
| `refactor/` | Code restructuring | `refactor/llm-service-interface` |

### Commit Messages (Conventional Commits)

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `chore`: Maintenance (CI, deps, config)
- `refactor`: Code change that neither fixes nor adds
- `test`: Adding or updating tests

**Scopes:** `cli`, `core`, `python`, `template`, `ci`, `docs`

**Examples:**
```
feat(cli): add --template flag for project scaffolding
fix(python): handle missing model file gracefully
chore(ci): use PowerShell commands on Windows runners
docs: update README with installation instructions
```

### Branch Protection Rules

The `main` branch is protected:
- Requires pull request before merging
- Requires CI checks to pass
- No direct pushes allowed

### Pull Request Workflow

1. **Create a branch** from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/my-feature
   ```

2. **Make changes** and commit with conventional commits

3. **Push and create PR**:
   ```bash
   git push -u origin feature/my-feature
   ```

4. **Run checks locally** before requesting review:
   ```bash
   pnpm lint
   pnpm typecheck
   pnpm test
   ```

5. **PR requirements**:
   - Descriptive title (conventional commit format)
   - Link to related issue if applicable
   - One feature or fix per PR
   - Update docs if changing public API

6. **After approval**, squash and merge to `main`

### Releases

Releases are tagged on `main`:

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

Version format: `vMAJOR.MINOR.PATCH` (semver)

- **MAJOR**: Breaking changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

---

## Useful Commands

```bash
# Development
pnpm install          # Install all dependencies
pnpm dev              # Run development servers
pnpm build            # Build all packages
pnpm test             # Run tests
pnpm typecheck        # TypeScript checking
pnpm format           # Format with Prettier

# Template testing
cd template
pnpm install
pnpm dev              # Start frontend + backend

# Python package
cd packages/tether-python
uv venv
uv pip install -e ".[dev]"
pytest
```
