#!/bin/bash

set -Eeuo pipefail

echo "=== Stock Tracking - Setup Script ==="
echo "This script prepares Python environment and optional system deps."
echo ""

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
WITH_SYSTEM_DEPS=false
for arg in "$@"; do
  case "$arg" in
    --install-system-deps)
      WITH_SYSTEM_DEPS=true
      ;;
  esac
done

if [ "$WITH_SYSTEM_DEPS" = true ]; then
  if command -v apt-get >/dev/null 2>&1; then
    echo "🔧 Installing system dependencies (apt)..."
    sudo apt-get update -y || true
    sudo apt-get install -y cmake build-essential || true
    # Optional GTK backend for pywebview
    sudo apt-get install -y python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0 || true
    # Optional Chromium app mode
    sudo apt-get install -y chromium-browser || sudo apt-get install -y chromium || true
  else
    echo "ℹ️  Skipping system dependencies (no apt-get)."
  fi
fi

echo "📦 Preparing Python virtual environment..."
if [ -d "$ROOT_DIR/venv" ]; then
  echo "➡️  Using existing venv at $ROOT_DIR/venv"
else
  python3 -m venv "$ROOT_DIR/venv"
  echo "✅ venv created"
fi

echo "📚 Installing Python requirements..."
source "$ROOT_DIR/venv/bin/activate"
python3 -m pip install --upgrade pip
python3 -m pip install -r "$ROOT_DIR/requirements.txt"
deactivate
echo "✅ Python requirements installed"

echo "💾 Ensuring database..."
if [ ! -f "$ROOT_DIR/inventory.db" ]; then
  source "$ROOT_DIR/venv/bin/activate"
  python3 "$ROOT_DIR/database.py"
  deactivate
  echo "✅ Database initialized"
else
  echo "➡️  Database already exists"
fi

echo "📁 Ensuring models directory..."
mkdir -p "$ROOT_DIR/models"
echo "➡️  Put your .gguf models under: $ROOT_DIR/models"

echo "✅ Setup completed. Next: ./run.sh"


