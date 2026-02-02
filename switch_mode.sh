#!/bin/bash
echo "Switching AI mode..."
if [ "$1" == "cloud" ]; then
    sed -i '' 's/ollama:/ollama:\n  cloud_model: "gpt-oss:120b-cloud"/' config/config.yaml
    echo "🌤️  Switched to CLOUD mode (gpt-oss:120b-cloud)"
elif [ "$1" == "local" ]; then
    sed -i '' 's/ollama:/ollama:\n  cloud_model: "llama3.1:8b-instruct"/' config/config.yaml
    echo "💻 Switched to LOCAL mode (llama3.1:8b-instruct)"
elif [ "$1" == "tunnel" ]; then
    echo "🌐 Starting with Cloudflare tunnel for external access..."
    echo "Run: ./start_with_tunnel.sh"
    echo "This will start the app and create a public URL for external access"
elif [ "$1" == "help" ]; then
    echo "Usage: ./switch_mode.sh [cloud|local|tunnel|help]"
    echo "  cloud  - Switch to cloud AI model"
    echo "  local  - Switch to local AI model"
    echo "  tunnel - Show tunnel setup instructions"
    echo "  help   - Show this help"
else
    echo "Usage: ./switch_mode.sh [cloud|local|tunnel|help]"
fi
