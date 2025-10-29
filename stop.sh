#!/bin/bash

set -Eeuo pipefail

echo "=== Stock Tracking - Stop Script ==="
echo ""

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "→ Stopping Flask (port 5000)"
if command -v fuser >/dev/null 2>&1; then
  fuser -k 5000/tcp 2>/dev/null || true
elif command -v lsof >/dev/null 2>&1; then
  lsof -ti:5000 2>/dev/null | xargs -r kill 2>/dev/null || true
else
  # Fallback: kill any process listening on port 5000
  pid="$(ss -ltnp 2>/dev/null | awk "/:5000 / {print \$6}" | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -n1 || true)"
  if [ -n "${pid:-}" ]; then
    echo "🛑 Stopping Flask on port 5000 (pid=$pid)"
    kill "$pid" 2>/dev/null || true
    sleep 1
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
  fi
fi

echo "✅ Flask stopped."

