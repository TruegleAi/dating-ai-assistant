# Munch AI Dating Assistant - Quickstart Guide

## Prerequisites

- **Python 3.12+**
- **Ollama Desktop App** (with cloud models enabled)
- **macOS/Linux** (Windows with WSL)

---

## 1. Quick Setup (5 minutes)

### Clone & Install

```bash
cd /Users/ducke.duck_1/dating-ai-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Ollama

Make sure Ollama Desktop is running, then verify your models:

```bash
ollama list
```

You should see cloud models like:
- `deepseek-v3.1:671b-cloud` (primary - best for conversations)
- `gemini-3-flash-preview:cloud` (fallback + vision for screenshots)

If you need to pull them:
```bash
ollama run deepseek-v3.1:671b-cloud "hi"
ollama run gemini-3-flash-preview:cloud "hi"
```

### Start the App

```bash
python app.py
```

You'll see:
```
✅ Assistant initialized with Ollama Desktop (Cloud Models)
   Primary: deepseek-v3.1:671b-cloud
   🔗 Connected! Using: deepseek-v3.1:671b-cloud
🚀 LAUNCHING MUNCH - AI DATING ASSISTANT
```

---

## 2. Access the App

- **Web UI**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs

---

## 3. Using the Web Interface

### Main Screen

1. **Paste messages** or **upload a screenshot** of your conversation
2. **Select response type** (Dating App, Text, DMs, etc.)
3. Click **"Analyze & Get Suggestion"**
4. Get AI-powered reply suggestions

### Sidebar Menu (☰ hamburger icon)

- **Chemistry Score** - Circular progress showing overall performance
- **Success/Failure Stats** - Track your wins and losses
- **AI Tip** - Personalized advice based on your conversations
- **Conversation History** - All your tracked conversations with status:
  - ✓ Success
  - ⏳ Stalled
  - 👻 Ghosted

### Creating Conversations

1. Open sidebar → Click **"+ New Conversation"**
2. Name it (e.g., "Sarah - Tinder")
3. Select the platform type
4. Now all messages you analyze will be saved to this conversation

---

## 4. API Endpoints

### Quick Analysis (no account needed)

```bash
# Get dating advice
curl -X POST http://localhost:5000/advice \
  -H "Content-Type: application/json" \
  -d '{"text": "She takes 2 days to reply. What should I do?"}'

# Analyze interest level
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"sender": "woman", "text": "haha that's funny 😂"}]}'

# Generate opener
curl -X POST http://localhost:5000/opener \
  -H "Content-Type: application/json" \
  -d '{"profile_context": "She loves hiking and has a dog", "platform": "tinder"}'
```

### Full Conversation Tracking

```bash
# Create user
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"email": "me@example.com"}'

# Create conversation
curl -X POST http://localhost:5000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "name": "Sarah", "response_type": "Dating App"}'

# Add messages
curl -X POST http://localhost:5000/api/conversations/1/messages \
  -H "Content-Type: application/json" \
  -d '{"role": "user", "content": "Hey! Love your hiking pics"}'

# Get AI suggestion
curl -X POST http://localhost:5000/api/ai/suggest \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": 1}'

# Analyze conversation
curl -X POST http://localhost:5000/api/conversations/1/analyze
```

---

## 5. Docker Deployment

```bash
# Start with Docker Compose
docker compose up -d

# View logs
docker compose logs -f munch-ai

# Stop
docker compose down
```

Access at http://localhost:8000

---

## 6. Environment Variables

Create a `.env` file for production:

```env
# Required for cloud models (if using Ollama cloud API)
OLLAMA_API_KEY=your_key_here

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-key-change-this
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional: Error tracking
SENTRY_DSN=https://xxx@sentry.io/xxx

# Optional: Redis caching
REDIS_URL=redis://localhost:6379/0
```

---

## 7. Troubleshooting

### "Can't connect to AI brain"
```bash
# Check Ollama is running
ollama list

# Test model directly
curl http://localhost:11434/api/chat -d '{
  "model": "deepseek-v3.1:671b-cloud",
  "messages": [{"role": "user", "content": "hi"}],
  "stream": false
}'
```

### Image upload not working
- Make sure `gemini-3-flash-preview:cloud` is available (it has vision)
- Check terminal for "Trying vision model:" debug output

### Slow responses
- Cloud models can take 10-30 seconds
- Check your internet connection
- Try a faster fallback model

---

## 8. File Structure

```
dating-ai-assistant/
├── app.py                 # Main FastAPI application
├── config/
│   └── config.yaml        # Model & app configuration
├── database/
│   ├── models.py          # SQLAlchemy models
│   └── database.py        # DB connection
├── services/
│   ├── analysis_service.py    # Conversation analysis
│   ├── auth_service.py        # JWT authentication
│   ├── cache_service.py       # Redis caching
│   ├── database_service.py    # CRUD operations
│   └── image_service.py       # Screenshot OCR
├── web_interface/
│   ├── index.html         # Main UI
│   ├── style.css          # Styling
│   └── app.js             # Frontend logic
├── requirements.txt       # Python dependencies
└── docker-compose.yml     # Container deployment
```

---

## Need Help?

- **API Documentation**: http://localhost:5000/docs
- **Health Check**: http://localhost:5000/health
- **GitHub Issues**: Report bugs and feature requests
