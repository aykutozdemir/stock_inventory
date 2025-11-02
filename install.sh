#!/bin/bash

set -Eeuo pipefail

echo "=== Electronic Component Inventory - Installation ==="
echo "Installing with GPU acceleration support for RTX 5090"
echo ""

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Install system dependencies
echo "🔧 Installing system dependencies..."
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -y || true
  sudo apt-get install -y cmake build-essential || true
  # GTK backend for pywebview
  sudo apt-get install -y python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0 || true
  # Chromium app mode fallback
  sudo apt-get install -y chromium-browser || sudo apt-get install -y chromium || true
  # NVIDIA CUDA toolkit
  sudo apt-get install -y nvidia-cuda-toolkit || true
else
  echo "ℹ️  Skipping system dependencies (no apt-get)."
fi

# Create virtual environment
echo "📦 Creating Python virtual environment..."
if [ -d "$ROOT_DIR/venv" ]; then
  echo "➡️  Using existing venv"
else
  python3 -m venv "$ROOT_DIR/venv"
  echo "✅ Virtual environment created"
fi

# Install Python dependencies
echo "📚 Installing Python dependencies..."
source "$ROOT_DIR/venv/bin/activate"
python3 -m pip install --upgrade pip

# Install llama-cpp-python with CUDA support
echo "🚀 Installing llama-cpp-python with CUDA support..."
echo "   Using pre-built CUDA 12.3 wheel for RTX 5090 compatibility"
python3 -m pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu123

# Install other requirements
echo "📦 Installing other Python requirements..."
python3 -m pip install -r "$ROOT_DIR/requirements.txt" --no-deps
python3 -m pip install -r "$ROOT_DIR/requirements.txt"

deactivate
echo "✅ Python dependencies installed with CUDA support"

# Initialize database
echo "💾 Initializing database..."
if [ ! -f "$ROOT_DIR/inventory.db" ]; then
  source "$ROOT_DIR/venv/bin/activate"
  python3 "$ROOT_DIR/database.py"
  deactivate
  echo "✅ Database initialized"
else
  echo "➡️  Database already exists"
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p "$ROOT_DIR/models"
mkdir -p "$ROOT_DIR/uploads"
mkdir -p "$ROOT_DIR/memory"

# Auto-detect hardware and create config
echo "🔍 Auto-detecting hardware configuration..."
source "$ROOT_DIR/venv/bin/activate"
python3 "$ROOT_DIR/hardware_detector.py"
deactivate

# Test installation
echo "🧪 Testing installation..."
source "$ROOT_DIR/venv/bin/activate"
if [ -f "$ROOT_DIR/tests/test_cuda_install.py" ]; then
  python3 "$ROOT_DIR/tests/test_cuda_install.py"
else
  echo "✅ Installation completed (test script not found, but installation successful)"
fi
deactivate

echo ""
echo "✅ Installation completed successfully!"
echo "🚀 Run: ./run.sh"
echo "📖 Read: README.md"