#!/bin/bash

set -Eeuo pipefail

echo "=== Electronic Component Inventory - Packaging ==="
echo ""

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PACKAGE_NAME="electronic-component-inventory-$(date +%Y%m%d-%H%M%S)"
PACKAGE_DIR="$ROOT_DIR/$PACKAGE_NAME"

echo "📦 Creating package: $PACKAGE_NAME"

# Create package directory
mkdir -p "$PACKAGE_DIR"

# Copy essential files
echo "📋 Copying application files..."
cp -r "$ROOT_DIR"/* "$PACKAGE_DIR/" 2>/dev/null || true

# Remove unnecessary files
echo "🧹 Cleaning up package..."
cd "$PACKAGE_DIR"
rm -rf venv/ 2>/dev/null || true
rm -rf __pycache__/ 2>/dev/null || true
rm -rf *.pyc 2>/dev/null || true
rm -rf .git/ 2>/dev/null || true
rm -rf models/*.gguf 2>/dev/null || true
rm -f inventory.db 2>/dev/null || true
rm -f hardware_config.json 2>/dev/null || true

# Remove test and development files
rm -f test_*.py 2>/dev/null || true
rm -f simple_tray_test.py 2>/dev/null || true
rm -f gpu_monitor.py 2>/dev/null || true
rm -f download_models.py 2>/dev/null || true
rm -f start_tray_daemon.sh 2>/dev/null || true
rm -f setup.sh 2>/dev/null || true
rm -f run_app.sh 2>/dev/null || true

# Create a clean requirements.txt without llama-cpp-python
echo "📝 Creating clean requirements.txt..."
cat > requirements.txt << 'EOF'
Flask==3.0.0
flask-cors==4.0.0
Werkzeug==3.0.1
requests==2.31.0

# LangChain local LLM
langchain
langchain-community
# llama-cpp-python - installed separately with CUDA support via install.sh
# Use: pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu123
pywebview

# GUI backend for pywebview (Qt)
PyQt5==5.15.10
PyQtWebEngine==5.15.7
qtpy==2.4.1

# GUI backend for pywebview (GTK) - alternative to avoid Qt MouseButtons bug
PyGObject==3.50.0

# System tray support
pystray==0.19.5
Pillow==10.0.0

# Hardware detection
psutil==5.9.0
EOF

# Create installation instructions
echo "📖 Creating installation instructions..."
cat > INSTALL.md << 'EOF'
# Installation Instructions

## Quick Start

1. **Install system dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y cmake build-essential python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0 chromium-browser nvidia-cuda-toolkit
   ```

2. **Install the application:**
   ```bash
   chmod +x install.sh run.sh stop.sh
   ./install.sh
   ```

3. **Run the application:**
   ```bash
   ./run.sh
   ```

## Features

- GPU-accelerated local LLM with CUDA support
- Auto-hardware detection and optimization
- System tray integration
- Electronic component inventory management
- AI-powered assistant with tools

## Requirements

- Python 3.11+
- NVIDIA GPU with CUDA 12.1+
- Linux desktop environment

## Commands

- `./install.sh` - Install application and dependencies
- `./run.sh` - Start application with system tray
- `./stop.sh` - Stop all application processes
- `./pack.sh` - Create distribution package

## Models

Place your .gguf models in the `models/` directory. The application will auto-detect and use them with GPU acceleration.
EOF

# Create archive
echo "🗜️  Creating archive..."
cd "$ROOT_DIR"
tar -czf "${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME"
rm -rf "$PACKAGE_DIR"

echo ""
echo "✅ Package created successfully!"
echo "📦 Archive: ${PACKAGE_NAME}.tar.gz"
echo "📏 Size: $(du -h "${PACKAGE_NAME}.tar.gz" | cut -f1)"
echo ""
echo "To install on another system:"
echo "1. Extract: tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "2. Install: cd $PACKAGE_NAME && ./install.sh"
echo "3. Run: ./run.sh"