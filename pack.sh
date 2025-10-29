#!/bin/bash

set -Eeuo pipefail

echo "=== Stock Tracking - Packaging Script ==="

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$ROOT_DIR/dist"
INCLUDE_MODELS=false

for arg in "$@"; do
  case "$arg" in
    --include-models)
      INCLUDE_MODELS=true
      ;;
  esac
done

mkdir -p "$DIST_DIR"
STAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE="$DIST_DIR/stock_tracking_${STAMP}.zip"

echo "📦 Creating: $ARCHIVE"

cd "$ROOT_DIR"

EXCLUDES=(
  "venv/*"
  "uploads/*"
  "__pycache__/*"
  ".git/*"
  "dist/*"
  "*.pyc"
  "*.pyo"
  "*.log"
  "inventory.db"
  "memory/agent_memory.json"
)

if [ "$INCLUDE_MODELS" = false ]; then
  EXCLUDES+=("models/*.gguf")
fi

ZIP_ARGS=()
for p in "${EXCLUDES[@]}"; do
  ZIP_ARGS+=( -x "$p" )
done

command -v zip >/dev/null 2>&1 || { echo "❌ zip utility not found. Install zip and retry."; exit 1; }

zip -r "$ARCHIVE" . \
  -i "app.py" "database.py" "index.html" "style.css" "script.js" \
     "requirements.txt" "README.md" \
     "install.sh" "run.sh" "stop.sh" "setup.sh" "pack.sh" "native_view.py" \
     "memory/*" "models/*" \
  "${ZIP_ARGS[@]}"

echo "✅ Package created: $ARCHIVE"


