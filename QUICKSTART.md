# 🚀 Munch AI - Quick Start Guide

**Version**: 5.1.0  
**Last Updated**: March 15, 2026

Get Munch AI Dating Assistant running in **5 minutes** or less!

---

## ⚡ Ultra Quick Start (Local Testing)

### 1. Clone & Setup (2 minutes)

```bash
# Clone repository
git clone https://github.com/your-username/dating-ai-assistant.git
cd dating-ai-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure (1 minute)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # Or use your favorite editor
```

**Minimum required keys:**
```bash
# OpenAI (for AI inference)
export OPENAI_API_KEY="sk-your-openai-api-key-here"

# YouTube (for knowledge base - optional)
export YOUTUBE_API_KEY="your-youtube-api-key-here"

# JWT Authentication (generate your own!)
export JWT_SECRET_KEY="$(openssl rand -hex 32)"
```

### 3. Run (30 seconds)

```bash
# Start the application
python3 app.py

# Or use the startup script
./start_app.sh
```

### 4. Access

Open your browser:
- **Web UI**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs
- **Health Check**: http://localhost:5000/health

---

## 🎯 Testing the Application

### Test via Web UI

1. Go to http://localhost:5000
2. Try the three main features:
   - **Get Advice**: Ask a dating question
   - **Analyze Interest**: Input conversation messages
   - **Generate Opener**: Describe a profile

### Test via API

```bash
# Health check
curl http://localhost:5000/health

# Get dating advice
curl -X POST http://localhost:5000/advice \
  -H "Content-Type: application/json" \
  -d '{"text": "She replied after 2 days. What should I do?"}'

# Analyze interest
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"sender": "woman", "text": "Hey! How are you? 😊"}
    ]
  }'

# Generate opener
curl -X POST http://localhost:5000/opener \
  -H "Content-Type: application/json" \
  -d '{
    "profile_context": "She loves hiking and dogs",
    "platform": "instagram"
  }'
```

### Run Test Suite

```bash
python3 test_app.py
```

---

## 🔧 Configuration Options

### AI Provider Selection

**Use OpenAI (Production)**:
```bash
export OPENAI_API_KEY="sk-..."
# App automatically uses OpenAI when key is present
```

**Use Ollama (Local/Development)**:
```bash
# Leave OPENAI_API_KEY empty
# Start Ollama Desktop app first
# App falls back to Ollama automatically
```

### Database Configuration

**SQLite (Development)**:
```bash
export DATABASE_URL="sqlite:///./munch_ai.db"
```

**PostgreSQL (Production)**:
```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/munch_db"
```

### CORS Configuration

**Local Development**:
```bash
export CORS_ALLOWED_ORIGINS="http://localhost:5000,http://localhost:3000"
```

**Production**:
```bash
export CORS_ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

---

## 📦 Docker Quick Start

### Run with Docker Compose

```bash
# Build and start all services (app + PostgreSQL + Redis)
docker-compose up -d

# View logs
docker-compose logs -f munch-ai

# Stop
docker-compose down
```

### Access

- **App**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

---

## 🆘 Troubleshooting

### Port Already in Use

```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use a different port
export PORT=8000
python3 app.py
```

### Missing Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### OpenAI API Errors

```bash
# Check your API key
echo $OPENAI_API_KEY

# Verify key is valid
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Database Errors

```bash
# Reset database
rm munch_ai.db
python3 -c "from database import init_db; init_db()"
```

### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

---

## 📚 Common Commands

```bash
# Start application
./start_app.sh

# Start with Cloudflare tunnel (external access)
./start_with_tunnel.sh

# Run tests
python3 test_app.py

# View logs
tail -f /tmp/munch_app.log

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Check health
curl http://localhost:5000/health
```

---

## 🎓 Next Steps

### After Local Testing

1. **Review Security Settings**
   - Generate new JWT_SECRET_KEY
   - Set production CORS origins
   - Remove debug logging

2. **Deploy to Production**
   - See `DEPLOYMENT_GUIDE.md` for complete instructions
   - Options: Railway, Render, or VPS

3. **Customize Legal Documents**
   - Edit `legal/PRIVACY_POLICY.md`
   - Edit `legal/TERMS_OF_SERVICE.md`
   - Add your contact information

4. **Set Up Monitoring**
   - Add SENTRY_DSN for error tracking
   - Configure uptime monitoring
   - Set up log aggregation

---

## 📖 Documentation Index

| Document | Purpose |
|----------|---------|
| `QUICKSTART.md` | You are here! |
| `DEPLOYMENT_GUIDE.md` | Production deployment instructions |
| `SECURITY_FIXES_SUMMARY.md` | Security improvements overview |
| `MUNCH_GUIDE.md` | Complete user guide |
| `README.md` | Project overview |
| `legal/PRIVACY_POLICY.md` | Privacy policy template |
| `legal/TERMS_OF_SERVICE.md` | Terms of service template |

---

## 🆘 Getting Help

### Documentation
- API Docs: http://localhost:5000/docs
- Full Guide: `MUNCH_GUIDE.md`
- Deployment: `DEPLOYMENT_GUIDE.md`

### Logs
```bash
# Application logs
tail -f /tmp/munch_app.log

# Docker logs
docker-compose logs -f munch-ai
```

### Health Checks
```bash
# Check if app is running
curl http://localhost:5000/health

# Check database
curl http://localhost:5000/api
```

---

## ✅ Quick Start Checklist

- [ ] Clone repository
- [ ] Create virtual environment
- [ ] Install dependencies
- [ ] Copy `.env.example` to `.env`
- [ ] Add OPENAI_API_KEY
- [ ] Generate JWT_SECRET_KEY
- [ ] Run `python3 app.py`
- [ ] Open http://localhost:5000
- [ ] Test all three features
- [ ] Run test suite

---

**Congratulations! Munch AI is running! 🎉**

For production deployment, see `DEPLOYMENT_GUIDE.md`.
