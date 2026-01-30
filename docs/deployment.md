# Deployment Guide

This guide covers building and distributing your Tether application.

## Build Process Overview

Building a Tether app involves three steps:

1. Build the React frontend
2. Build the Python backend (PyInstaller)
3. Build the Tauri app (includes both)

## Prerequisites

### All Platforms

- Node.js 18+
- Python 3.11+
- Rust toolchain
- uv package manager

### macOS

```bash
xcode-select --install
```

### Windows

- Visual Studio C++ Build Tools
- WebView2 Runtime

### Linux

```bash
# Ubuntu/Debian
sudo apt install libwebkit2gtk-4.1-dev build-essential
```

## Building

### 1. Install Dependencies

```bash
pnpm install
cd src-python && uv sync && cd ..
```

### 2. Build Python Backend

```bash
pnpm python:build
```

This creates `src-tauri/binaries/api-{target}`.

### 3. Build Application

```bash
pnpm tauri:build
```

Output locations:

- **macOS**: `src-tauri/target/release/bundle/dmg/`
- **Windows**: `src-tauri/target/release/bundle/msi/` or `nsis/`
- **Linux**: `src-tauri/target/release/bundle/deb/` or `appimage/`

## Platform-Specific Builds

### macOS

#### Universal Binary (Intel + ARM)

Build for both architectures:

```bash
# Build for ARM (Apple Silicon)
pnpm python:build
pnpm tauri:build --target aarch64-apple-darwin

# Build for Intel
pnpm python:build  # Rebuild for Intel
pnpm tauri:build --target x86_64-apple-darwin
```

#### Code Signing

For distribution outside the App Store:

1. Get an Apple Developer ID certificate
2. Set environment variables:

```bash
export APPLE_SIGNING_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
export APPLE_ID="your@email.com"
export APPLE_PASSWORD="app-specific-password"
export APPLE_TEAM_ID="YOUR_TEAM_ID"
```

3. Build with signing:

```bash
pnpm tauri:build
```

### Windows

#### Code Signing

For SmartScreen reputation:

1. Get an EV code signing certificate
2. Configure in `tauri.conf.json`:

```json
{
  "bundle": {
    "windows": {
      "certificateThumbprint": "YOUR_CERT_THUMBPRINT",
      "timestampUrl": "http://timestamp.digicert.com"
    }
  }
}
```

### Linux

AppImage is recommended for broad compatibility:

```bash
pnpm tauri:build --bundles appimage
```

## CI/CD with GitHub Actions

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  build:
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: macos-latest
            target: aarch64-apple-darwin
          - os: macos-13
            target: x86_64-apple-darwin
          - os: windows-latest
            target: x86_64-pc-windows-msvc
          - os: ubuntu-22.04
            target: x86_64-unknown-linux-gnu

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Setup pnpm
        uses: pnpm/action-setup@v3
        with:
          version: 9

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.target }}

      - name: Install dependencies (Linux)
        if: matrix.os == 'ubuntu-22.04'
        run: |
          sudo apt-get update
          sudo apt-get install -y libwebkit2gtk-4.1-dev libayatana-appindicator3-dev librsvg2-dev

      - name: Install dependencies
        run: |
          pnpm install
          cd src-python && uv sync

      - name: Build Python backend
        run: pnpm python:build

      - name: Build Tauri app
        uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tagName: v__VERSION__
          releaseName: "v__VERSION__"
          releaseBody: "See the assets for download links."
          releaseDraft: true
          prerelease: false
          args: --target ${{ matrix.target }}
```

## Distribution Checklist

### Before Release

- [ ] Update version in `package.json`
- [ ] Update version in `src-tauri/tauri.conf.json`
- [ ] Update version in `src-python/pyproject.toml`
- [ ] Test on all target platforms
- [ ] Verify LLM functionality works
- [ ] Check app icons are present

### macOS

- [ ] Sign the application
- [ ] Notarize with Apple
- [ ] Test on fresh macOS install

### Windows

- [ ] Sign the executable
- [ ] Test on fresh Windows install
- [ ] Verify SmartScreen doesn't block

### Linux

- [ ] Test AppImage on different distros
- [ ] Verify permissions are correct

## Bundle Size

Expected sizes:

- **Python backend binary**: 50-150 MB
- **Final installer**: 80-200 MB

### Reducing Size

1. Use smaller Python dependencies
2. Exclude unused packages from PyInstaller
3. Use UPX compression (experimental)

## Auto-Updates

Tauri supports auto-updates. Add to `tauri.conf.json`:

```json
{
  "plugins": {
    "updater": {
      "pubkey": "YOUR_PUBLIC_KEY",
      "endpoints": [
        "https://your-server.com/updates/{{target}}/{{arch}}/{{current_version}}"
      ]
    }
  }
}
```

See [Tauri Updater docs](https://tauri.app/v1/guides/distribution/updater/) for details.

## Troubleshooting

### Build fails on macOS

```bash
# Reset Xcode tools
sudo xcode-select --reset
```

### PyInstaller issues

```bash
# Rebuild with verbose output
cd src-python
uv run pyinstaller --onefile --name api --log-level DEBUG app/main.py
```

### Tauri build fails

```bash
# Check Rust targets
rustup target list --installed

# Add missing target
rustup target add x86_64-apple-darwin
```

### Binary not found

Ensure the binary name matches `tauri.conf.json`:

- Binary: `api-aarch64-apple-darwin`
- Config: `"externalBin": ["binaries/api"]`
