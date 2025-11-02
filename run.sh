#!/bin/bash

set -Eeuo pipefail

echo "=== Electronic Component Inventory - Starting ==="
echo ""

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if virtual environment exists
if [ ! -d "$ROOT_DIR/venv" ]; then
    echo "❌ Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "tray_app.py" 2>/dev/null || true
pkill -f "app.py" 2>/dev/null || true

# Auto-detect hardware configuration on first run
if [ ! -f "$ROOT_DIR/hardware_config.json" ]; then
    echo "🔍 First run detected - analyzing your hardware..."
    source "$ROOT_DIR/venv/bin/activate"
    python3 "$ROOT_DIR/hardware_detector.py"
    deactivate
    echo ""
fi

echo "🚀 Starting Electronic Component Inventory with system tray..."
echo "Look for the icon in your system tray (desktop bar)!"
echo "The tray icon should appear in the bottom-right area of your screen."
echo "Right-click the icon to access menu options."
echo ""
echo "Press Ctrl+C to quit the application."

# Start the application with system tray
source "$ROOT_DIR/venv/bin/activate"
# Print the selected model filename prior to launching
if [ -f "$ROOT_DIR/print_selected_model.py" ]; then
    python3 "$ROOT_DIR/print_selected_model.py" || true
fi
python3 "$ROOT_DIR/tray_app.py"