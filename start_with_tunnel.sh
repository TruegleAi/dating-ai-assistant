#!/bin/bash
# Dating AI Assistant with Cloudflare Tunnel - Startup Script
# User: Duck E. Duck (therealduckyduck@gmail.com)

echo "=================================================="
echo "  Dating AI Assistant + Cloudflare Tunnel"
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

# Start the application in background
echo "Starting Dating AI Assistant..."
python3 app.py > /tmp/munch_app.log 2>&1 &
APP_PID=$!

# Wait a moment for the app to start
sleep 3

# Check if the app started successfully
if ps -p $APP_PID > /dev/null; then
    echo "✅ Application started with PID: $APP_PID"
else
    echo "❌ Failed to start application"
    exit 1
fi

# Check if cloudflared is available
if command -v cloudflared &> /dev/null; then
    echo "Starting Cloudflare tunnel..."
    
    # Start cloudflared tunnel in background
    cloudflared tunnel --url http://localhost:5000 > /tmp/munch_tunnel.log 2>&1 &
    TUNNEL_PID=$!
    
    # Wait a moment for the tunnel to establish
    sleep 3
    
    # Check if tunnel started successfully
    if ps -p $TUNNEL_PID > /dev/null; then
        echo "✅ Cloudflare tunnel started with PID: $TUNNEL_PID"
        echo "Tunnel logs available at: /tmp/munch_tunnel.log"
        
        # Get the tunnel URL
        TUNNEL_URL=$(cloudflared tunnel info 2>/dev/null | grep -o 'https://[^ ]*\.trycloudflare\.com' | head -1)
        if [ ! -z "$TUNNEL_URL" ]; then
            echo "🌐 External access available at: $TUNNEL_URL"
        fi
    else
        echo "⚠️  Could not start Cloudflare tunnel automatically"
        echo "   You can start it manually with: cloudflared tunnel --url http://localhost:5000"
    fi
else
    echo "⚠️  Cloudflared not found. Install it to enable external access:"
    echo "   macOS: brew install cloudflare/cloudflare/cloudflared/cloudflared"
    echo "   Linux: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
fi

echo ""
echo "=================================================="
echo "  Application is running!"
echo "  Local access: http://localhost:5000"
if [ ! -z "$TUNNEL_URL" ]; then
    echo "  External access: $TUNNEL_URL"
fi
echo "=================================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    if ps -p $APP_PID > /dev/null; then
        kill $APP_PID 2>/dev/null
    fi
    if command -v cloudflared &> /dev/null && ps -p $TUNNEL_PID > /dev/null; then
        kill $TUNNEL_PID 2>/dev/null
    fi
    echo "Services stopped."
    exit 0
}

# Trap signals to ensure cleanup
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait $APP_PID $TUNNEL_PID 2>/dev/null