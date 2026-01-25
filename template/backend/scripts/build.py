"""
PyInstaller build script for creating standalone Python backend binary.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def get_binary_name() -> str:
    """Get the binary name for the current platform."""
    system = platform.system().lower()
    if system == "windows":
        return "api.exe"
    return "api"


def get_target_triple() -> str:
    """Get the target triple for the current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        if machine == "arm64":
            return "aarch64-apple-darwin"
        return "x86_64-apple-darwin"
    elif system == "windows":
        return "x86_64-pc-windows-msvc"
    elif system == "linux":
        return "x86_64-unknown-linux-gnu"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def build() -> None:
    """Build the Python backend using PyInstaller."""
    # Get paths
    backend_dir = Path(__file__).parent.parent
    src_tauri = backend_dir.parent / "src-tauri"
    target_triple = get_target_triple()
    binary_name = get_binary_name()

    # Create output directory
    output_dir = src_tauri / "binaries"
    output_dir.mkdir(parents=True, exist_ok=True)

    # PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        "api",
        "--distpath",
        str(output_dir),
        "--workpath",
        str(backend_dir / "build"),
        "--specpath",
        str(backend_dir),
        "--clean",
        str(backend_dir / "app" / "main.py"),
    ]

    print(f"Building Python backend for {target_triple}...")
    print(f"Command: {' '.join(cmd)}")

    # Run PyInstaller
    result = subprocess.run(cmd, cwd=backend_dir)

    if result.returncode != 0:
        print("PyInstaller build failed!")
        sys.exit(1)

    # Rename binary with target triple (required by Tauri)
    src_binary = output_dir / binary_name
    dst_binary = output_dir / f"api-{target_triple}{'.exe' if platform.system() == 'Windows' else ''}"

    if src_binary.exists():
        src_binary.rename(dst_binary)
        print(f"Binary created: {dst_binary}")
    else:
        print(f"Error: Binary not found at {src_binary}")
        sys.exit(1)

    # Clean up
    spec_file = backend_dir / "api.spec"
    if spec_file.exists():
        spec_file.unlink()

    build_dir = backend_dir / "build"
    if build_dir.exists():
        import shutil
        shutil.rmtree(build_dir)

    print("Build complete!")


if __name__ == "__main__":
    build()
