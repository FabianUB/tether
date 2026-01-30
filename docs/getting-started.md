# Getting Started with Tether

Tether is a template for building AI/ML desktop applications using Tauri, React, and Python. This guide will help you create your first Tether app.

## Prerequisites

Before you begin, make sure you have the following installed:

- **Node.js 18+** - [Download](https://nodejs.org/)
- **Python 3.11+** - [Download](https://www.python.org/)
- **uv** - Fast Python package manager - [Install](https://docs.astral.sh/uv/getting-started/installation/)
- **Rust** - Required for Tauri - [Install](https://www.rust-lang.org/tools/install)
- **pnpm** (recommended) - [Install](https://pnpm.io/installation)

### Platform-specific requirements

#### macOS

```bash
xcode-select --install
```

#### Windows

- Install [Microsoft Visual Studio C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Install [WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)

#### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget file libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev

# Fedora
sudo dnf install webkit2gtk4.1-devel openssl-devel curl wget file libappindicator-gtk3-devel librsvg2-devel
```

## Create a New Project

The easiest way to create a new Tether project is using the CLI:

```bash
npx create-tether-app my-app
```

You'll be prompted to choose:

1. **Project name** - The name of your project
2. **ML backend** - Local LLM, OpenAI API, or Custom
3. **Include example** - Whether to include a chat component example

## Project Structure

```
my-app/
├── src/                    # React frontend
│   ├── components/         # React components
│   ├── hooks/              # Custom React hooks
│   ├── App.tsx             # Main application
│   └── main.tsx            # Entry point
├── src-python/             # Python backend
│   ├── app/
│   │   ├── routes/         # API endpoints
│   │   └── services/       # Business logic (LLM service)
│   └── scripts/            # Build scripts
├── src-tauri/              # Tauri/Rust layer
│   └── src/
│       ├── main.rs         # Tauri entry point
│       └── sidecar.rs      # Python process management
├── package.json
├── pyproject.toml
└── .env.example
```

## Development Workflow

### Install Dependencies

```bash
cd my-app

# Install Node.js dependencies
pnpm install

# Install Python dependencies
cd src-python && uv sync && cd ..
```

### Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` to configure your LLM backend:

```env
# For local LLM
TETHER_LLM_BACKEND=local
TETHER_MODEL_PATH=./models/your-model.gguf

# For OpenAI
TETHER_LLM_BACKEND=openai
OPENAI_API_KEY=sk-your-api-key
```

### Run Development Servers

**Option 1: Separate terminals (recommended for development)**

```bash
# Terminal 1: Frontend with hot reload
pnpm dev

# Terminal 2: Python backend with hot reload
pnpm python:dev
```

**Option 2: Full Tauri development**

```bash
pnpm tauri:dev
```

## Building for Production

### 1. Build the Python Backend

```bash
pnpm python:build
```

This creates a standalone binary in `src-tauri/binaries/`.

### 2. Build the Application

```bash
pnpm tauri:build
```

The installer will be created in `src-tauri/target/release/bundle/`.

## Next Steps

- [Frontend Guide](./frontend-guide.md) - Learn how to build React UIs
- [Backend Guide](./backend-guide.md) - Learn how to work with Python/ML
- [Deployment Guide](./deployment.md) - Learn how to distribute your app
