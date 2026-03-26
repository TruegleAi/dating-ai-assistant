# Dating AI Assistant - Quick Start Guide
**User: Duck E. Duck (therealduckyduck@gmail.com)**

## Status: ✅ All Systems Working

Your dating AI assistant has been tested and is fully operational!

---

## Starting the Application

### Option 1: Using the Startup Script (Recommended)
```bash
./start_app.sh
```

This script will:
- Check and activate the virtual environment
- Kill any existing instances on port 5000
- Start the Dating AI Assistant

### Option 2: Manual Start
```bash
source venv/bin/activate
python3 app.py
```

---

## Testing the Application

Run the comprehensive test suite:
```bash
python3 test_app.py
```

This will test all endpoints:
- ✅ Health Check
- ✅ Dating Advice
- ✅ Interest Analysis
- ✅ Opener Generator

---

## Available API Endpoints

**Base URL:** `http://localhost:5000`

### 1. Health Check
```bash
curl http://localhost:5000/health
```

### 2. Get Dating Advice
```bash
curl -X POST http://localhost:5000/advice \
  -H "Content-Type: application/json" \
  -d '{
    "text": "She took 2 days to reply. What should I do?",
    "context": ["Push-Pull Dynamics"],
    "user_type": "premium"
  }'
```

### 3. Analyze Interest Level
```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"sender": "user", "text": "Hey! How are you?"},
      {"sender": "woman", "text": "Good! What about you? 😊"},
      {"sender": "user", "text": "Doing great!"},
      {"sender": "woman", "text": "That's awesome! What have you been up to?"}
    ]
  }'
```

### 4. Generate Premium Opener
```bash
curl -X POST http://localhost:5000/opener \
  -H "Content-Type: application/json" \
  -d '{
    "profile_context": "She loves traveling and photography",
    "platform": "instagram"
  }'
```

---

## Interactive API Documentation

Visit the auto-generated API docs:
- **Swagger UI:** http://localhost:5000/docs
- **ReDoc:** http://localhost:5000/redoc

---

## Configuration

Your API keys are configured in:
- `config/config.yaml` - Main configuration
- `.env` - Environment variables (backup)

**Current Configuration:**
- AI Model: `gpt-oss:120b-cloud`
- Port: `5000`
- YouTube Channels: 5 curated sources

---

## Troubleshooting

### Port 5000 Already in Use
```bash
# Kill the process using port 5000
lsof -ti:5000 | xargs kill -9

# Then restart the app
./start_app.sh
```

### Dependencies Missing
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Check Logs
```bash
tail -f /tmp/app_output.log
```

---

## Test Results (Latest Run)

✅ **Health Check**: PASSED
✅ **Dating Advice**: PASSED
✅ **Interest Analysis**: PASSED
✅ **Opener Generator**: PASSED

**All systems operational!**

---

## Notes

- ✅ No mock users or test data found in the codebase
- ✅ All dependencies installed correctly
- ✅ App connects successfully to Ollama Cloud API
- ✅ All endpoints tested and working

If you need to add a test user for your own testing, use:
- **Name:** Duck E. Duck
- **Email:** therealduckyduck@gmail.com

---

## Next Steps

1. Start the app: `./start_app.sh`
2. Visit the docs: http://localhost:5000/docs
3. Test the API using the examples above
4. Build your frontend or integrate with your existing app

---

**Happy Dating! 🚀**
