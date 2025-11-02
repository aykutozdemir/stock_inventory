#!/bin/bash

echo "=== Electronic Component Inventory - Stopping ==="
echo ""

# Kill all related processes
echo "🛑 Stopping all application processes..."

# Stop tray application
pkill -f "tray_app.py" 2>/dev/null && echo "✅ Stopped tray application" || echo "ℹ️  Tray application not running"

# Stop launch script
pkill -f "launch_with_tray.py" 2>/dev/null && echo "✅ Stopped launch script" || echo "ℹ️  Launch script not running"

# Stop Flask app
pkill -f "app.py" 2>/dev/null && echo "✅ Stopped Flask application" || echo "ℹ️  Flask application not running"

# Stop any remaining Python processes related to this app
pkill -f "electronic-component-inventory" 2>/dev/null && echo "✅ Stopped remaining processes" || true

echo ""
echo "✅ All processes stopped successfully!"
echo "💡 Run ./run.sh to start again"