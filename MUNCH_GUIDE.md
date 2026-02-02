# 🎯 Munch - AI Dating Assistant

**Brand Identity**: Clean, modern, playful dating AI with real psychology-backed advice

## 🎨 Brand Colors

- **Primary Background**: `#1a1d2e` (Dark Navy)
- **Secondary Background**: `#252836` (Charcoal)
- **Card Background**: `#2a2d3e` (Slate)
- **Yellow/Orange**: `#FFB800` → `#FF8C00` (Primary CTA)
- **Cyan**: `#00D4FF` (Accents)
- **Pink**: `#FF3366` (Highlights)
- **Text Primary**: `#ffffff`
- **Text Secondary**: `#b4b4b4`

## 🚀 Quick Start

### Start the App
```bash
./start_app.sh
```

### Access Points
- **Web Interface**: http://localhost:5000
- **API Documentation**: http://localhost:5000/docs
- **API Endpoint**: http://localhost:5000/api

## ✨ Features

### 1. Get Dating Advice
AI-powered advice based on dating psychology, attraction dynamics, and social proof principles.

**Usage**: Ask any dating question and get detailed, actionable advice.

### 2. Analyze Interest Level
Evaluate message exchanges to determine her interest level (High/Medium/Low) with suggested reply timing.

**Usage**: Input conversation messages and get an interest score out of 100 plus strategic advice.

### 3. Generate Opening Lines
Create unforgettable, psychology-backed opening lines tailored to profile details and platforms.

**Usage**: Describe her profile and select platform to get a premium opener with expected success rate.

## 🧪 Testing

### Run Full Test Suite
```bash
python3 test_app.py
```

### Manual API Testing
```bash
# Get dating advice
curl -X POST http://localhost:5000/advice \
  -H "Content-Type: application/json" \
  -d '{
    "text": "She replied after 2 days. What should I do?",
    "context": ["Push-Pull Dynamics"],
    "user_type": "premium"
  }'

# Analyze interest
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"sender": "user", "text": "Hey! How are you?"},
      {"sender": "woman", "text": "Good! What about you? 😊"}
    ]
  }'

# Generate opener
curl -X POST http://localhost:5000/opener \
  -H "Content-Type: application/json" \
  -d '{
    "profile_context": "She loves hiking and photography",
    "platform": "instagram"
  }'
```

## 📁 Project Structure

```
dating-ai-assistant/
├── app.py                   # Main FastAPI application
├── config/
│   └── config.yaml          # API keys and configuration
├── web_interface/
│   ├── index.html           # Web UI (Munch branded)
│   ├── style.css            # Munch brand styling
│   ├── app.js               # Frontend logic
│   └── logo.png             # Munch logo
├── scripts/
│   └── youtube_collector.py # Knowledge base builder
├── data/
│   └── processed/           # Knowledge base data
├── start_app.sh             # Easy startup script
├── test_app.py              # Comprehensive test suite
└── requirements.txt         # Python dependencies
```

## 🔧 Configuration

### API Keys
Edit `config/config.yaml`:
```yaml
youtube:
  api_key: "YOUR_YOUTUBE_API_KEY"

ollama:
  cloud_model: "gpt-oss:120b-cloud"
  api_key: "YOUR_OLLAMA_API_KEY"

app:
  host: "0.0.0.0"
  port: 5000
```

### YouTube Knowledge Sources
5 curated channels provide dating psychology knowledge:
- PsychologicalShadows
- Darkpsychologyy
- Francesca Psychology
- AlphaMaleStrategies
- BasedZeus

## 🎯 Core Psychology Principles

The AI is trained on these attraction dynamics:

1. **Push-Pull Dynamics**: Creating attraction through attention variability
2. **Qualification**: Having her prove value rather than seeking validation
3. **Social Proof**: Demonstrating value indirectly through lifestyle
4. **Cold Reading**: Making personalized, seemingly insightful observations
5. **Fractionation**: Rapid emotional pacing to build connection

## 🐛 Troubleshooting

### Port 5000 In Use
```bash
lsof -ti:5000 | xargs kill -9
./start_app.sh
```

### Missing Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### API Connection Issues
Check that:
1. API keys are valid in `config/config.yaml`
2. Internet connection is active
3. Ollama Cloud API is accessible

### View Logs
```bash
tail -f /tmp/munch_app.log
```

## 📊 System Status

✅ **API**: Fully functional
✅ **Web Interface**: Munch branded & operational
✅ **AI Model**: Connected to Ollama Cloud (gpt-oss:120b-cloud)
✅ **All Endpoints**: Tested and working
✅ **No Mock Data**: Production-ready prototype

## 👤 Test User

For testing purposes:
- **Name**: Duck E. Duck
- **Email**: therealduckyduck@gmail.com

## 🚀 Next Steps

1. **Launch**: `./start_app.sh`
2. **Open**: http://localhost:5000
3. **Test**: Try all three features
4. **Customize**: Adjust branding/features as needed
5. **Deploy**: Ready for production deployment

## 📞 Support

For issues or questions, check:
- `/tmp/munch_app.log` for application logs
- `http://localhost:5000/docs` for API documentation
- `test_app.py` for working examples

---

**Munch** - Your AI-powered dating wingman 🎯
