---
title: Munch GPT
emoji: 🧲
colorFrom: pink
colorTo: red
sdk: docker
app_port: 8000
pinned: false
---

# 🧲 Munch - Dating AI Assistant

A cloud-powered AI assistant that provides dating advice and psychology-based messaging strategies, trained on curated YouTube content about attraction and social dynamics.

## ✨ Features
- **Psychology-Based Advice**: Uses principles from dark psychology, attraction theory, and social dynamics. 
- **Interest Analysis**: Analyzes message patterns to gauge her interest level.
- **Premium Openers**: Generates unforgettable opening lines tailored to her profile.
- **YouTube Knowledge Base**: Context from specialized dating/psychology channels.
- **External Access**: Cloudflare tunnel support for remote access
- **CORS Enabled**: Cross-origin resource sharing for web applications

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Cloudflare account (for external access)

### Installation
1. **Clone & Setup**:
   ```bash
   git clone https://github.com/truegleai/dating-ai-assistant.git
   cd dating-ai-assistant
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   Copy the example config and add your API keys:
   ```bash
   cp config/config.yaml.example config/config.yaml
   # Edit config/config.yaml with your API keys
   ```

3. **Start the Application**:
   ```bash
   ./start_app.sh
   ```

## 🌐 External Access with Cloudflare Tunnel

To access your application from external networks:

1. **Install Cloudflared** (if not already installed):
   ```bash
   # macOS
   brew install cloudflare/cloudflare/cloudflared/cloudflared
   
   # Ubuntu/Debian
   curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared.deb
   ```

2. **Start with Tunnel**:
   ```bash
   ./start_with_tunnel.sh
   ```
   
   This will start both the application and create a public URL accessible from anywhere.

3. **Alternative Method**:
   You can also run the tunnel separately:
   ```bash
   # Start the app normally
   ./start_app.sh
   
   # In another terminal, start the tunnel
   cloudflared tunnel --url http://localhost:5000
   ```

## 🛠️ Scripts Overview

- `start_app.sh`: Starts the application locally on port 5000
- `start_with_tunnel.sh`: Starts the application and Cloudflare tunnel for external access
- `setup_tunnel.sh`: Creates Cloudflare tunnel configuration
- `switch_mode.sh`: Switch between cloud/local AI models or show tunnel info
- `test_app.py`: Comprehensive test suite

## 🧪 Testing

Run the test suite to verify all functionality:
```bash
python3 test_app.py
```

## 🔧 Configuration

The application uses `config/config.yaml` for all settings:
- `app.host`: Host address (default: "0.0.0.0")
- `app.port`: Port number (default: 5000)
- `ollama.cloud_model`: AI model to use
- `ollama.api_key`: Ollama Cloud API key
- `youtube.api_key`: YouTube Data API key

## 🌍 CORS Configuration

The application is configured to accept cross-origin requests from any domain:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
```

This enables remote web applications to access the API without CORS errors.

## 📡 API Endpoints

- `GET /`: Web UI
- `GET /api`: API documentation
- `GET /health`: Health check
- `POST /advice`: Get dating advice
- `POST /analyze`: Analyze interest level
- `POST /opener`: Generate premium opener
- `GET /docs`: Interactive API documentation

## 🤖 AI Models

Switch between AI models using:
```bash
./switch_mode.sh cloud    # Use cloud model
./switch_mode.sh local    # Use local model
./switch_mode.sh tunnel   # Show tunnel instructions
```

## 🚀 Deployment

For production deployment:
1. Use a reverse proxy (nginx/Apache) with SSL
2. Or use the Cloudflare tunnel for quick external access
3. Configure proper domain and SSL certificates

## 📚 Documentation

- `MUNCH_GUIDE.md`: Complete user guide
- `QUICK_START.md`: Quick reference
- `DEPLOYMENT_SUMMARY.md`: Full deployment details

## 🐛 Troubleshooting

- **Port in use**: `lsof -ti:5000 | xargs kill -9`
- **Check status**: `curl http://localhost:5000/health`
- **View logs**: `tail -f /tmp/munch_app.log`
- **Tunnel logs**: `tail -f /tmp/munch_tunnel.log`

## 📞 Support

For issues or questions, check the documentation files or contact the development team.