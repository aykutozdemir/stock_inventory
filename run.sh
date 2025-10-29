#!/bin/bash

echo "=== Stock Tracking - Run Script ==="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found. Please run './install.sh' first."
    exit 1
fi

echo "ℹ️  Using LangChain local LLM."

# Check if database exists
if [ ! -f "inventory.db" ]; then
    echo "⚠️  Database not found. Initializing..."
    source venv/bin/activate
    python3 database.py
    deactivate
    echo "✅ Database initialized."
    echo ""
fi

# Kill any existing Flask server on port 5000
echo "🛑 Stopping any existing server..."
if command -v fuser &> /dev/null; then
    fuser -k 5000/tcp > /dev/null 2>&1
elif command -v lsof &> /dev/null; then
    lsof -ti:5000 | xargs kill -9 > /dev/null 2>&1
fi
sleep 1

# Activate virtual environment and run the app
echo "🚀 Starting Flask application..."
echo ""
source venv/bin/activate

# Get the local IP address
if command -v hostname &> /dev/null; then
    LOCAL_IP=$(hostname -I | awk '{print $1}')
else
    LOCAL_IP="localhost"
fi

echo "========================================="
echo "  Stock Tracking Application"
echo "========================================="
echo "📱 Web Interface:"
echo "  Local:  http://localhost:5000"
echo "  Network: http://$LOCAL_IP:5000"
echo ""
echo "📱 Mobile Access:"
echo "  1. Connect phone to same network"
echo "  2. Open: http://$LOCAL_IP:5000"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo "========================================="
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    
    # Kill Flask
    if [ ! -z "$FLASK_PID" ]; then
        kill $FLASK_PID 2>/dev/null
    fi
    
    # Optionally stop Docker containers
    echo "   (Docker containers remain running. Use 'docker-compose down' to stop them)"
    echo ""
    
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Start Flask app in background
python3 app.py &
FLASK_PID=$!

# Wait for Flask to be ready
echo "⏳ Waiting for Flask server..."
sleep 2

# Check if server is ready
MAX_WAIT=20
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s http://localhost:5000 > /dev/null 2>&1; then
        echo "✅ Flask server is ready!"
        break
    fi
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done
echo ""

# Open native window if PyWebview is available; else fallback to browser
if python3 -c "import webview" >/dev/null 2>&1; then
    echo "🪟 Opening native window (no browser chrome)..."
    APP_URL="http://localhost:5000" python3 native_view.py &
else
    if command -v xdg-open &> /dev/null; then
        echo "🌐 Opening browser..."
        xdg-open http://localhost:5000 2>/dev/null &
    elif command -v open &> /dev/null; then
        echo "🌐 Opening browser..."
        open http://localhost:5000 2>/dev/null &
    fi
fi

# Show logs
echo "📋 Server logs (Ctrl+C to stop):"
echo ""

# Wait for Flask process
wait $FLASK_PID
