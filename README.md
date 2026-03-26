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
- **CORS Enabled**: Cross-origin resource sharing for web applications

## 🚀 Quick Start

### Prerequisites
- Python 3.12+

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
   source .env
   uvicorn app:app --reload --port 8000
   ```

## 🛠️ Scripts Overview

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

Set `GROQ_API_KEY` in your `.env` to use Groq (recommended). Falls back to Ollama if not set.

## 🚀 Deployment

For production deployment:
1. Use a reverse proxy (nginx/Apache) with SSL
2. Configure proper domain and SSL certificates

## 📚 Documentation

- `MUNCH_GUIDE.md`: Complete user guide
- `QUICK_START.md`: Quick reference
- `DEPLOYMENT_SUMMARY.md`: Full deployment details

## 🐛 Troubleshooting

- **Port in use**: `lsof -ti:5000 | xargs kill -9`
- **Check status**: `curl http://localhost:5000/health`
- **View logs**: `tail -f /tmp/munch_app.log`

## 📞 Support

For issues or questions, check the documentation files or contact the development team.