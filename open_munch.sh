#!/bin/bash
# Quick launcher for Munch web interface

echo "🚀 Opening Munch..."
open http://localhost:5000

# Check if app is running
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Munch is running!"
else
    echo "⚠️  Munch is not running. Starting now..."
    ./start_app.sh
    sleep 3
    open http://localhost:5000
fi
