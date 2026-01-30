# Development Guide

Tips for faster development builds and better developer experience.

## Cargo Build Optimization

Rust/Tauri builds can be slow, especially the first build. Here's how to speed things up.

### First Build vs Incremental

- **First build**: Downloads and compiles all dependencies. This is unavoidable.
- **Incremental builds**: Only recompiles changed code. Much faster.

The included `.cargo/config.toml` is already configured for fast incremental builds.

### Using sccache (Recommended)

sccache caches compiled artifacts across projects, dramatically speeding up builds.

**Install:**

```bash
# macOS
brew install sccache

# Linux
cargo install sccache

# Windows
cargo install sccache
```

**Enable:**

```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export RUSTC_WRAPPER=sccache
```

After enabling, your second build of any Rust project will be much faster.

### Using a Faster Linker

The default linker is slow. Alternative linkers can cut link times significantly.

**macOS (lld via LLVM):**

```bash
brew install llvm
```

Then uncomment the macOS section in `src-tauri/.cargo/config.toml`.

**Linux (mold):**

```bash
# Ubuntu/Debian
sudo apt install mold

# Fedora
sudo dnf install mold

# Arch
sudo pacman -S mold
```

Then uncomment the Linux section in `src-tauri/.cargo/config.toml`.

### Expected Build Times

With optimizations enabled:

| Build Type | First Build | Incremental |
| ---------- | ----------- | ----------- |
| Debug      | 2-5 min     | 5-30 sec    |
| Release    | 5-10 min    | 1-3 min     |

Times vary based on hardware. M1/M2 Macs and modern Linux machines are typically faster.

## Frontend Development

### Hot Module Replacement (HMR)

Vite provides instant HMR for React components. Changes appear immediately without full page reload.

### Running Frontend Only

For UI-only development, you can run just the frontend:

```bash
cd frontend
pnpm dev
```

Note: API calls will fail without the backend. Use this for pure UI work.

## Backend Development

### Running Backend Only

Test the Python backend independently:

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

The `--reload` flag enables auto-restart on code changes.

### Testing API Endpoints

With the backend running, test endpoints directly:

```bash
# Health check
curl http://localhost:8000/health

# Chat (requires model loaded)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

Or use the interactive docs at http://localhost:8000/docs

## Running Everything Together

```bash
# From project root
pnpm dev
```

This starts:

- Frontend dev server (Vite)
- Backend server (uvicorn)
- Tauri dev window

## Debugging

### Frontend (React)

Use browser DevTools in the Tauri window:

- Right-click > Inspect
- Or use the keyboard shortcut (Cmd+Opt+I on macOS)

### Backend (Python)

Add print statements or use a debugger:

```python
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()  # Pause until debugger attaches
```

Then attach VS Code's Python debugger to port 5678.

### Rust (Tauri)

For Rust debugging, use VS Code with the CodeLLDB extension:

1. Set breakpoints in `.rs` files
2. Run "Debug" configuration
3. Step through code

## Common Issues

### "Port already in use"

Another process is using the port. Find and kill it:

```bash
# Find process on port 8000
lsof -i :8000

# Kill it
kill -9 <PID>
```

### "Model not found"

For Ollama:

```bash
ollama pull llama3.2
```

For local models, ensure the GGUF file path is correct in your settings.

### Slow Rust Builds

1. Enable sccache (see above)
2. Use a faster linker (see above)
3. Ensure you're using `cargo build` not `cargo build --release` during development
4. Check that incremental compilation is enabled (default in our config)
