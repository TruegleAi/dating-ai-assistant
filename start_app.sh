#!/bin/bash
# Dating AI Assistant - Startup Script
# User: Duck E. Duck (therealduckyduck@gmail.com)

echo "=================================================="
echo "  Dating AI Assistant - Starting..."
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Activate virtual environment
source venv/bin/activate

# Check if config file exists
if [ ! -f "config/config.yaml" ]; then
    echo "❌ config/config.yaml not found!"
    echo "Please copy config/config.yaml.template to config/config.yaml"
    echo "and add your API keys."
    exit 1
fi

# Kill any existing instances on port 5000
echo "Checking for existing instances..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
sleep 1

# Start the application
echo "Starting Dating AI Assistant..."
echo ""

# Show instructions for external access
echo "💡 For external access via Cloudflare tunnel, run:"
echo "   ./start_with_tunnel.sh"
echo ""

python3 app.py

# Cleanup on exit
trap "echo 'Shutting down...'; lsof -ti:5000 | xargs kill -9 2>/dev/null; exit" INT TERM
