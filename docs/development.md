# Development Guide

Tips for faster development builds and better developer experience.

## Cargo Build Optimization

Rust/Tauri builds can be slow, especially the first build. Here's how to speed things up.

### What's Already Configured

The included `.cargo/config.toml` has these optimizations enabled by default:

| Setting | Effect | Platforms |
|---------|--------|-----------|
| `opt-level = 0` | Skip optimizations in dev | All |
| `incremental = true` | Only recompile changed code | All |
| `codegen-units = 256` | Parallelize compilation | All |
| `split-debuginfo = unpacked` | Faster linking | macOS, Linux (auto-detected) |
| Dependencies at `opt-level = 2` | Pre-optimize deps | All |

Platform-specific settings are auto-applied based on your target architecture.

### Quick Wins (No Installation)

These are already enabled. Just make sure you're running **debug builds** during development:

```bash
# Good - uses dev profile (fast)
pnpm tauri:dev
cargo build

# Slow - use only for final builds
pnpm build:app
cargo build --release
```

### sccache (Highly Recommended)

sccache caches compiled artifacts across **all** your Rust projects. After installing, subsequent builds of any project reuse cached artifacts.

**Install:**

```bash
# macOS
brew install sccache

# Linux/Windows
cargo install sccache
```

**Enable permanently:**

```bash
# Add to your shell profile (~/.zshrc, ~/.bashrc, etc.)
export RUSTC_WRAPPER=sccache
```

**Verify it's working:**

```bash
sccache --show-stats
```

### Faster Linker (Optional)

Linking is often the slowest part of incremental builds. A faster linker can cut build times by 30-50%.

**macOS (lld via LLVM):**

```bash
brew install llvm
```

Then update the rustflags in `src-tauri/.cargo/config.toml` for your architecture:

```toml
[target.aarch64-apple-darwin]  # or x86_64-apple-darwin for Intel
rustflags = ["-C", "split-debuginfo=unpacked", "-C", "link-arg=-fuse-ld=/opt/homebrew/opt/llvm/bin/ld64.lld"]
```

**Linux (mold):**

```bash
# Ubuntu/Debian
sudo apt install mold

# Fedora
sudo dnf install mold

# Arch
sudo pacman -S mold
```

Then update the rustflags in `src-tauri/.cargo/config.toml`:

```toml
[target.x86_64-unknown-linux-gnu]  # or aarch64-unknown-linux-gnu for ARM
rustflags = ["-C", "split-debuginfo=unpacked", "-C", "link-arg=-fuse-ld=mold"]
```

**Windows:**

Windows uses the MSVC linker by default. Alternative linkers are not commonly used.

### Expected Build Times

| Build Type | First Build | With sccache | Incremental |
|------------|-------------|--------------|-------------|
| Debug | 2-5 min | 30-60 sec* | 5-30 sec |
| Release | 5-10 min | 2-4 min* | 1-3 min |

*After first build when cache is warm.

Times vary based on hardware. Apple Silicon Macs are typically 2-3x faster than Intel.

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
