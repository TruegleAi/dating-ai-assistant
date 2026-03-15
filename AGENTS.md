# AGENTS.md - Development Guide for AI Assistants

This file contains essential information for agentic coding agents working in this repository.

## 🏗️ Build/Test/Lint Commands

### Running Tests
- **Run full test suite**: `python3 test_app.py`
- **Run CORS tests**: `python3 test_cors.py`
- **Manual API testing**: Use the interactive test suite in `test_app.py`

### Development Server
- **Start locally**: `./start_app.sh` (runs on http://localhost:5000)
- **Start with tunnel**: `./start_with_tunnel.sh` (creates external access)
- **Health check**: `curl http://localhost:5000/health`

### Application Management
- **Switch AI modes**: `./switch_mode.sh [cloud|local|tunnel]`
- **Setup tunnel**: `./setup_tunnel.sh`
- **View logs**: `tail -f /tmp/munch_app.log` or `tail -f /tmp/munch_tunnel.log`

## 📁 Project Structure

```
dating-ai-assistant/
├── app.py                    # Main FastAPI application
├── config/
│   └── config.yaml          # Live configuration (API keys, settings)
├── requirements.txt          # Python dependencies
├── test_app.py              # Comprehensive test suite
├── test_cors.py             # CORS functionality tests
├── web_interface/           # Frontend HTML/CSS/JS
├── scripts/
│   └── youtube_collector.py # YouTube data collection utilities
└── data/                    # Knowledge base and processed data
```

## 🎯 Application Architecture

### Core Components
- **FastAPI Application**: Main web server with CORS enabled
- **DatingAssistant Class**: Core AI logic using Ollama Cloud API
- **Pydantic Models**: Request/response validation (`MessageRequest`, `InterestAnalysis`, `OpenerRequest`)
- **YouTube Integration**: Knowledge base from curated psychology/dating channels

### API Endpoints
- `GET /health` - Health check
- `POST /advice` - Get dating advice
- `POST /analyze` - Analyze interest level from message history
- `POST /opener` - Generate personalized opening lines
- `GET /` - Web UI interface

## 🐍 Code Style Guidelines

### Python Formatting & Conventions
- **Python Version**: 3.12+ (specified in README)
- **Style**: Follow PEP 8 with descriptive variable names
- **Import Organization**: Standard library → third-party → local imports
- **Type Hints**: Use `typing` module for function signatures and class attributes
- **Docstrings**: Use triple-quoted strings for function and class documentation

### Code Structure Patterns
```python
# Import organization example
import os
import json
from datetime import datetime
from typing import List, Optional

import yaml
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Class definition with type hints
class DatingAssistant:
    def __init__(self) -> None:
        self.config = self._load_config()
    
    def _private_method(self) -> bool:
        """Private methods use underscore prefix"""
        return True
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `DatingAssistant`, `MessageRequest`)
- **Functions/Variables**: `snake_case` (e.g., `analyze_interest`, `api_key`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`)
- **Private Methods**: Prefix with underscore (`_test_connection`)

### Error Handling Patterns
```python
# API request error handling
try:
    response = requests.post(url, headers=headers, json=payload, timeout=90)
    response.raise_for_status()
    return response.json()['message']['content']
except requests.exceptions.RequestException as e:
    print(f"❌ API Error: {e}")
    return "Service temporarily unavailable"
```

### Configuration Management
- Use YAML configuration in `config/config.yaml`
- Load config at application startup with proper error handling
- Never commit sensitive API keys to version control
- Use environment variables or secure config management for production

### API Response Patterns
```python
# Standard success response structure
return {
    "score": score,
    "level": level,
    "advice": advice,
    "reply_time": self.reply_timing[level],
    "analyzed_messages": len(recent_msgs)
}

# Error responses raise HTTPException
raise HTTPException(status_code=500, detail="AI service unavailable")
```

## 🔧 Development Workflow

### Before Making Changes
1. **Read existing code patterns** in `app.py` to understand the structure
2. **Check the configuration** in `config/config.yaml` for available settings
3. **Run tests** to ensure current functionality works: `python3 test_app.py`

### Adding New Features
1. **Add Pydantic models** for request/response validation
2. **Update FastAPI routes** with proper HTTP status codes
3. **Add corresponding tests** in `test_app.py`
4. **Update this AGENTS.md** if adding new development commands

### Testing Requirements
- **Always test endpoints** manually after changes using `test_app.py`
- **Verify CORS functionality** with `test_cors.py` if modifying web interfaces
- **Check configuration loading** when modifying config structure

## 📝 Configuration Details

### Critical Config Sections
- `ollama.cloud_model`: AI model name (e.g., "gpt-oss:120b-cloud")
- `ollama.api_key`: Ollama Cloud API authentication
- `youtube.api_key`: YouTube Data API for knowledge base
- `app.host`/`app.port`: Server binding configuration

### Environment Setup
```bash
# Virtual environment setup
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy and configure settings
cp config.yaml.example config.yaml  # (if template exists)
# Edit config.yaml with your API keys
```

## 🚀 Deployment Notes

### Production Considerations
- Use HTTPS/reverse proxy for production
- Set proper CORS origins instead of wildcard (`*`)
- Use secure credential management (not config files)
- Monitor logs in `/tmp/munch_app.log`

### Cloudflare Tunnel Setup
The project includes built-in tunnel support for external access:
- Tunnel creates public URL that forwards to localhost:5000
- Useful for testing web applications from external domains
- Configure with `./setup_tunnel.sh` and run with `./start_with_tunnel.sh`

## 🧪 Key Dependencies

### Core Framework
- `fastapi==0.109.2` - Web framework
- `uvicorn==0.27.1` - ASGI server
- `pydantic` - Data validation

### AI & Data Processing
- `transformers==4.38.0` - Hugging Face transformers
- `torch==2.2.1` - PyTorch for ML
- `sentence-transformers==2.2.2` - Text embeddings
- `openai==1.12.0` - OpenAI API client

### Utilities
- `python-dotenv==1.0.1` - Environment variables
- `pyyaml==6.0.1` - YAML configuration
- `requests==2.31.0` - HTTP client

## ⚠️ Security Notes

- **Never commit API keys** to version control
- **Use environment variables** for production credentials
- **CORS is set to wildcard** (`*`) - restrict origins in production
- **Validate all inputs** using Pydantic models
- **Implement rate limiting** for production API usage

## 🔄 Maintenance Tasks

### Regular Updates
- Keep `requirements.txt` dependencies updated
- Monitor API key usage and rotation
- Update YouTube channel list in configuration
- Review and refresh knowledge base data

### Performance Monitoring
- Monitor AI API response times
- Check tunnel connectivity if using external access
- Review log files for errors: `/tmp/munch_app.log`
- Test endpoints after any configuration changes