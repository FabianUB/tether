# Rust Usage in Tether

How Rust is used in Tether, what each file does, and how the pieces connect. **No Rust knowledge required.**

---

## Table of Contents

1. [Why Rust?](#why-rust)
2. [What Does Rust Do in Tether?](#what-does-rust-do-in-tether)
3. [File Structure](#file-structure)
4. [Key Concepts](#key-concepts)
5. [File-by-File Breakdown](#file-by-file-breakdown)
6. [How Frontend Talks to Rust](#how-frontend-talks-to-rust)
7. [The Application Lifecycle](#the-application-lifecycle)
8. [Common Scenarios](#common-scenarios)
9. [When Would You Modify Rust Code?](#when-would-you-modify-rust-code)

---

## Why Rust?

Tether uses [Tauri](https://tauri.app), a framework for building desktop apps. Tauri is written in Rust and provides:

- **Small bundle size**: ~10MB vs ~150MB for Electron
- **Native performance**: Compiled code, not interpreted
- **Security**: Memory-safe by design
- **Cross-platform**: macOS, Windows, Linux from one codebase

**The good news**: You rarely need to touch Rust code. It's the "invisible" layer.

---

## What Does Rust Do in Tether?

The Rust layer handles exactly three things:

```
┌─────────────────────────────────────────────────────────────┐
│                     RUST / TAURI LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  1. Window Management     → Creates the desktop window       │
│  2. Sidecar Management    → Starts/stops the Python backend  │
│  3. IPC Bridge            → Lets frontend ask for the port   │
└─────────────────────────────────────────────────────────────┘
```

That's it. All business logic lives in React (frontend) and Python (backend).

---

## File Structure

```
src-tauri/
├── Cargo.toml              # Rust dependencies (like package.json)
├── tauri.conf.json         # Tauri configuration
├── build.rs                # Build script (runs before compilation)
├── binaries/               # Where the Python binary goes
│   └── api-{target}        # e.g., api-aarch64-apple-darwin
├── icons/                  # App icons for all platforms
└── src/
    ├── main.rs             # Entry point, app setup
    └── sidecar.rs          # Python process management
```

---

## Key Concepts

### Tauri

Tauri is like Electron but lighter. Instead of bundling Chromium, it uses the system's built-in webview (WebKit on macOS, WebView2 on Windows).

```
┌─────────────────────────────────────────┐
│              Your App                    │
├──────────────────┬──────────────────────┤
│   React Frontend │    Rust Backend      │
│   (runs in       │    (native code)     │
│    webview)      │                      │
├──────────────────┴──────────────────────┤
│         System Webview                   │
│   (Safari/Edge engine, not Chromium)    │
└─────────────────────────────────────────┘
```

### Sidecar

A **sidecar** is an external binary that Tauri can spawn and manage. In Tether, the sidecar is the Python backend (compiled with PyInstaller).

```
┌─────────────┐         ┌─────────────┐
│   Tauri     │ spawns  │   Python    │
│   (Rust)    │────────>│   Backend   │
│             │         │  (sidecar)  │
└─────────────┘         └─────────────┘
       │                       │
       │    manages lifecycle  │
       │    (start/stop/port)  │
       └───────────────────────┘
```

### IPC (Inter-Process Communication)

Tauri provides a way for the frontend (JavaScript) to call Rust functions. These are called **commands**.

```typescript
// Frontend (TypeScript)
const port = await invoke("get_api_port");
```

```rust
// Backend (Rust)
#[tauri::command]
async fn get_api_port(...) -> Result<u16, String> {
    // Returns the port number
}
```

---

## File-by-File Breakdown

### `Cargo.toml` — Dependencies

```toml
[dependencies]
tauri = { version = "2", features = ["devtools"] }  # Core framework
tauri-plugin-shell = "2"                            # For spawning sidecar
tokio = { version = "1", features = ["sync"] }      # Async runtime
portpicker = "0.1"                                  # Find available ports
```

This is like `package.json` for Rust. You rarely modify this.

---

### `tauri.conf.json` — Configuration

Key sections explained:

```json
{
  "build": {
    "beforeDevCommand": "pnpm dev", // Runs before dev mode
    "beforeBuildCommand": "pnpm build:all", // Runs before production build
    "devUrl": "http://localhost:1420", // Vite dev server URL
    "frontendDist": "../dist" // Built frontend location
  },
  "bundle": {
    "externalBin": ["binaries/api"] // The Python sidecar binary
  }
}
```

The `externalBin` is crucial — it tells Tauri to bundle the Python binary with the app.

---

### `build.rs` — Build Script

```rust
fn main() {
    tauri_build::build()
}
```

This runs before Rust compilation. It:

- Generates Rust code from `tauri.conf.json`
- Sets up the build environment

You never modify this file.

---

### `src/main.rs` — Application Entry Point

This is where the app starts. Let's break it down:

#### Line 1-2: Windows Console Hiding

```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
```

Translation: "On Windows release builds, don't show a console window."

#### Lines 11-23: IPC Commands

```rust
#[tauri::command]
async fn get_api_port(state: tauri::State<'_, Arc<Mutex<SidecarManager>>>) -> Result<u16, String> {
    let manager = state.lock().await;
    Ok(manager.port())
}
```

This is a **command** the frontend can call:

| Part                       | Meaning                                       |
| -------------------------- | --------------------------------------------- |
| `#[tauri::command]`        | "This function can be called from JavaScript" |
| `state: tauri::State<...>` | Access to shared app state                    |
| `Arc<Mutex<...>>`          | Thread-safe wrapper (like a lock)             |
| `Result<u16, String>`      | Returns a port number or an error message     |

#### Lines 25-64: App Setup

```rust
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())   // Enable sidecar support
        .setup(|app| {
            // 1. Find an available port
            let port = portpicker::pick_unused_port().expect("No available port");

            // 2. Create sidecar manager
            let manager = Arc::new(Mutex::new(SidecarManager::new(port)));

            // 3. Store in app state (so commands can access it)
            app.manage(manager.clone());

            // 4. Start the Python backend
            tauri::async_runtime::spawn(async move {
                manager.lock().await.start(&app_handle).await;
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            // When window closes, stop the Python backend
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                // ... stop sidecar ...
            }
        })
        .invoke_handler(tauri::generate_handler![get_api_port, restart_backend])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

**Lifecycle summary:**

1. App starts → Find available port
2. Create sidecar manager → Store in app state
3. Spawn Python backend → Pass it the port
4. Window closes → Kill Python backend

---

### `src/sidecar.rs` — Python Process Manager

This file manages the Python backend's lifecycle.

#### The SidecarManager Struct

```rust
pub struct SidecarManager {
    child: Option<CommandChild>,  // The running process (or None)
    port: u16,                    // Port the backend runs on
}
```

Think of this as a class with two properties:

- `child`: The Python process (null if not running)
- `port`: Which port it's using

#### Starting the Sidecar

```rust
pub async fn start(&mut self, app: &AppHandle) -> Result<String, String> {
    let shell = app.shell();
    let (mut rx, child) = shell
        .sidecar("api")                              // Find binary named "api"
        .args(["--port", &self.port.to_string()])    // Pass port as argument
        .spawn()                                      // Start the process
        .map_err(|e| format!("Failed: {}", e))?;

    // ... handle output ...

    self.child = Some(child);
    Ok("Started")
}
```

This:

1. Finds the `api` binary in `binaries/`
2. Runs it with `--port 12345` argument
3. Stores the process handle

#### Stopping the Sidecar

```rust
pub fn stop(&mut self) -> Result<String, String> {
    if let Some(child) = self.child.take() {
        // Platform-specific process killing
        #[cfg(unix)]
        {
            // On macOS/Linux: pkill child processes
        }

        #[cfg(windows)]
        {
            // On Windows: taskkill /F /T
        }

        child.kill()?;
    }
    Ok("Stopped")
}
```

The `#[cfg(unix)]` and `#[cfg(windows)]` are **compile-time conditionals**. Only the relevant code is included for each platform.

#### Automatic Cleanup

```rust
impl Drop for SidecarManager {
    fn drop(&mut self) {
        let _ = self.stop();
    }
}
```

`Drop` is Rust's destructor. When the app closes, this ensures the Python process is killed.

---

## How Frontend Talks to Rust

The frontend uses Tauri's `invoke` function:

```typescript
// frontend/src/hooks.ts
import { invoke } from "@tauri-apps/api/core";

export async function getApiPort(): Promise<number> {
  return await invoke("get_api_port");
}
```

This calls the Rust function `get_api_port` and returns the port number.

**Flow:**

```
React Component
      │
      ▼
invoke('get_api_port')
      │
      ▼
Tauri IPC Bridge
      │
      ▼
Rust: get_api_port()
      │
      ▼
Returns port (e.g., 54321)
      │
      ▼
Frontend uses: http://127.0.0.1:54321/api/chat
```

---

## The Application Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                        APP STARTUP                               │
├─────────────────────────────────────────────────────────────────┤
│  1. User double-clicks app icon                                  │
│  2. Tauri (Rust) starts                                          │
│  3. Rust finds available port (e.g., 54321)                      │
│  4. Rust spawns Python binary: ./api --port 54321                │
│  5. Python backend starts FastAPI server on port 54321           │
│  6. Tauri opens window, loads React frontend                     │
│  7. React calls invoke('get_api_port') → gets 54321              │
│  8. React makes HTTP requests to http://127.0.0.1:54321          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        APP SHUTDOWN                              │
├─────────────────────────────────────────────────────────────────┤
│  1. User closes window                                           │
│  2. Tauri receives CloseRequested event                          │
│  3. Rust calls sidecar.stop()                                    │
│  4. Python process is terminated                                 │
│  5. App exits cleanly                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Common Scenarios

### "The Python backend isn't starting"

Check:

1. Is the binary in `src-tauri/binaries/`?
2. Is it named correctly? (e.g., `api-aarch64-apple-darwin` on M1 Mac)
3. Check Tauri logs for errors

### "Frontend can't connect to backend"

The frontend might be trying to connect before the backend is ready:

```typescript
// Wait for backend to be healthy
async function waitForBackend(port: number, maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/health`);
      if (res.ok) return true;
    } catch {}
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}
```

### "How do I add a new IPC command?"

1. Add the function in `main.rs`:

```rust
#[tauri::command]
async fn my_new_command() -> Result<String, String> {
    Ok("Hello from Rust!".into())
}
```

2. Register it in the handler:

```rust
.invoke_handler(tauri::generate_handler![get_api_port, restart_backend, my_new_command])
```

3. Call from frontend:

```typescript
const result = await invoke("my_new_command");
```

---

## When Would You Modify Rust Code?

**Almost never.** Here are the rare cases:

| Scenario                                         | What to modify                               |
| ------------------------------------------------ | -------------------------------------------- |
| Add new IPC command                              | `main.rs` — add `#[tauri::command]` function |
| Change window settings                           | `tauri.conf.json` — modify `app.windows`     |
| Add native feature (file dialogs, notifications) | `Cargo.toml` — add Tauri plugin              |
| Change app icon                                  | Replace files in `icons/` folder             |

For everything else (UI, API logic, LLM integration), stay in React and Python.

---

## Quick Reference

| Rust Syntax     | Meaning                                     |
| --------------- | ------------------------------------------- |
| `fn`            | Function definition                         |
| `async fn`      | Asynchronous function                       |
| `let`           | Variable declaration (immutable)            |
| `let mut`       | Mutable variable                            |
| `->`            | Return type                                 |
| `Result<T, E>`  | Returns `T` on success, `E` on error        |
| `Option<T>`     | Either `Some(value)` or `None`              |
| `#[...]`        | Attribute (like decorator in Python)        |
| `impl`          | Implementation block (methods for a struct) |
| `pub`           | Public (visible outside module)             |
| `&`             | Reference (borrow)                          |
| `Arc<Mutex<T>>` | Thread-safe shared ownership with lock      |
| `.await`        | Wait for async operation                    |
| `?`             | Return early if error                       |

---

## Summary

The Rust layer in Tether is intentionally minimal:

- **~150 lines of code** total
- **Two files** with actual logic (`main.rs`, `sidecar.rs`)
- **One job**: Start Python, give frontend the port, stop Python on exit

You can build entire applications without ever reading this code. But now you know what it does.
