#!/bin/bash

set -Eeuo pipefail

echo "=== Stock Tracking - Installation Script (LangChain local LLM) ==="
echo ""

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Python environment (project runtime) ---
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old venv..."
    rm -rf venv
fi

echo "📦 Creating virtual environment..."
python3 -m venv venv
echo "✅ Virtual environment created successfully."

echo ""
echo "📚 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Python dependencies installed."

echo ""
echo "💾 Initializing database..."
if [ ! -f "inventory.db" ]; then
    python3 database.py
    echo "✅ Database initialized."
else
    echo "✅ Database already exists."
fi

# --- Tooling checks (no sudo) ---
echo ""
echo "🔧 Checking required tools (git, curl)..."
for cmd in git curl; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "❌ $cmd not found. Please install $cmd and re-run."
        exit 1
    fi
done
echo "✅ Tools OK."

# --- LangChain local LLM setup ---
echo ""
echo "🧠 Setting up local model for LangChain (llama.cpp) ..."
MODELS_DIR="$ROOT_DIR/models"
mkdir -p "$MODELS_DIR"

GGUF_COUNT=$(find "$MODELS_DIR" -maxdepth 1 -type f -iname '*.gguf' | wc -l | tr -d ' ')
if [ "$GGUF_COUNT" = "0" ]; then
  echo "📥 No .gguf models found in $MODELS_DIR"
  echo "   Downloading a small test model (TinyLlama 1.1B Q4_K_M) for convenience..."
  TINY="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
  curl -L -o "$MODELS_DIR/$TINY" "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf?download=true" || true
  if [ -f "$MODELS_DIR/$TINY" ]; then
    echo "✅ Downloaded: $MODELS_DIR/$TINY"
  else
    echo "⚠️  Could not download automatically. Please place a .gguf model under $MODELS_DIR or set LLM_MODEL to an absolute path."
  fi
else
  echo "✅ Found $GGUF_COUNT .gguf model(s) in $MODELS_DIR"
fi

# --- Project directories ---
echo ""
echo "📂 Creating required project directories..."
mkdir -p memory uploads static
echo "✅ Directories ready."

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "Next steps:"
echo "- Place your preferred .gguf model in $MODELS_DIR (or export LLM_MODEL=/abs/path/model.gguf)"
echo "- Run the app: ./run.sh"
echo "- Test API: curl -s -X POST http://localhost:5000/api/ai/ask -H 'Content-Type: application/json' -d '{"question":"Merhaba!"}'"
echo ""
