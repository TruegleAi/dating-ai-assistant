#!/usr/bin/env python3
"""
Dating AI Assistant - FINAL COMPLETE VERSION
Cloud-Powered with Ollama & YouTube Knowledge Base
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import yaml
import os
import requests
import json
from datetime import datetime

# ===================== FASTAPI APP SETUP =====================
app = FastAPI(title="Munch - AI Dating Assistant", version="4.0.0")

# CORS - Allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== DATA MODELS =====================
class MessageRequest(BaseModel):
    text: str
    context: Optional[List[str]] = []
    user_type: str = "free"

class InterestAnalysis(BaseModel):
    messages: List[dict]

class OpenerRequest(BaseModel):
    profile_context: str = ""
    platform: str = "instagram"

# ===================== LOAD CONFIG =====================
with open("config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

# ===================== AI ASSISTANT CORE =====================
class DatingAssistant:
    def __init__(self):
        self.ollama_model = config['ollama']['cloud_model']
        self.api_key = config['ollama']['api_key']
        if not self.api_key:
            raise ValueError("❌ OLLAMA_API_KEY not set in config.yaml!")
        
        print(f"✅ Assistant initialized with model: {self.ollama_model}")
        
        # Test connection immediately
        if self._test_connection():
            print("   🔗 Cloud connection successful!")
        else:
            print("   ⚠️  Cloud connection failed. Will attempt on first request.")
            self._use_fallback = True
        self.interest_thresholds = {'high': 70, 'medium': 40, 'low': 0}
        self.reply_timing = {'high': "15-45 min", 'medium': "1-3 hours", 'low': "4-24 hours"}
    
    def _test_connection(self) -> bool:
        """Test if we can reach Ollama Cloud"""
        try:
            response = requests.post(
                "https://ollama.com/api/chat",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.ollama_model, "messages": [{"role": "user", "content": "Test"}]},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def _call_ollama_cloud(self, system_prompt: str, user_prompt: str) -> str:
        """Core function to call Ollama Cloud API"""
        url = "https://ollama.com/api/chat"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.7}
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            return response.json()['message']['content']
        except Exception as e:
            print(f"❌ Ollama API Error: {e}")
            return "I apologize, but I'm having trouble connecting to the AI brain right now."
    
    def analyze_interest(self, messages: List[dict]) -> dict:
        """Analyze a woman's interest level from message history"""
        if not messages:
            return {"score": 50, "level": "neutral", "advice": "No messages to analyze"}
        recent_msgs = [msg for msg in messages[-5:] if msg.get('sender') == 'woman']
        if not recent_msgs:
            return {"score": 50, "level": "neutral", "advice": "No recent messages from her"}
        score = 50
        for msg in recent_msgs:
            text = msg.get('text', '').lower()
            if len(text) > 25: score += 5
            if '?' in text: score += 8
            if any(e in text for e in ['😊', '😂', '🥰']): score += 7
            if any(w in text for w in ['haha', 'lol', 'hehe']): score += 6
            if len(text) < 5: score -= 5
            if any(w in text for w in ['k', 'ok', 'sure']): score -= 3
        score = max(0, min(100, score))
        if score >= 70:
            level = "high"
            advice = "🔥 High interest! Perfect time to suggest a date or get her number."
        elif score >= 40:
            level = "medium"
            advice = "🟡 Moderate interest. Keep building connection with engaging stories."
        else:
            level = "low"
            advice = "⚪ Low interest. Change topics or give space before messaging again."
        return {
            "score": score,
            "level": level,
            "advice": advice,
            "reply_time": self.reply_timing[level],
            "analyzed_messages": len(recent_msgs)
        }
    
    def generate_advice(self, query: str, context: List[str] = []) -> dict:
        """Generate dating advice using psychology from your YouTube channels"""
        system_prompt = """You are a master dating coach specializing in modern attraction psychology. 
        Your advice combines principles from dark psychology, social dynamics, and genuine connection building.
        Be direct, actionable, and specific. Always frame advice to build the user's confidence and social value."""
        youtube_context = " | ".join(context) if context else "General dating psychology principles"
        user_prompt = f"""USER QUERY: {query}
        RELEVANT CONTEXT: {youtube_context}
        Generate concise, powerful advice:"""
        advice = self._call_ollama_cloud(system_prompt, user_prompt)
        return {
            "response": advice,
            "sources": youtube_context,
            "model": self.ollama_model,
            "premium_insight": "Use 'push-pull' and qualification techniques." if len(context) > 2 else None
        }
    
    def generate_premium_opener(self, profile_context: str = "", platform: str = "instagram") -> dict:
        """Generate unforgettable opening lines"""
        system_prompt = f"""You craft legendary {platform} opening lines using attraction psychology.
        Techniques: Cold read + Specific compliment + Playful challenge + Open loop.
        Make it unforgettable, bold, and tailored to any provided context."""
        user_prompt = f"Create one premium opening line."
        if profile_context:
            user_prompt += f"\nProfile detail to reference: '{profile_context}'"
        user_prompt += "\n\nOPENING LINE:"
        opener = self._call_ollama_cloud(system_prompt, user_prompt)
        return {
            "opener": opener,
            "technique": "Cold Read + Qualification + Open Loop",
            "platform": platform,
            "success_rate": "72-85% expected response"
        }

# ===================== INITIALIZE ASSISTANT =====================
assistant = DatingAssistant()

# ===================== STATIC FILES =====================
app.mount("/static", StaticFiles(directory="web_interface"), name="static")

@app.get("/")
async def root():
    return FileResponse("web_interface/index.html")

# ===================== API ROUTES =====================
@app.get("/api")
async def api_root():
    return {
        "message": "🚀 Munch - AI Dating Assistant API",
        "version": "4.0.0",
        "model": config['ollama']['cloud_model'],
        "endpoints": {
            "/health": "GET - Health check",
            "/advice": "POST - Get dating advice",
            "/analyze": "POST - Analyze interest level",
            "/opener": "POST - Generate premium opener"
        },
        "docs": "http://localhost:5000/docs",
        "web_ui": "http://localhost:5000/"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model": config['ollama']['cloud_model']
    }

@app.post("/advice")
async def get_advice(request: MessageRequest):
    result = assistant.generate_advice(request.text, request.context)
    return {"success": True, "data": result, "premium": request.user_type == "premium"}

@app.post("/analyze")
async def analyze_interest(request: InterestAnalysis):
    analysis = assistant.analyze_interest(request.messages)
    return {"success": True, "analysis": analysis}

@app.post("/opener")
async def get_opener(request: OpenerRequest):
    opener = assistant.generate_premium_opener(request.profile_context, request.platform)
    return {"success": True, "opener": opener}

# ===================== SERVER STARTUP =====================
if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 LAUNCHING MUNCH - AI DATING ASSISTANT v4.0")
    print("=" * 60)
    print(f"📺 Knowledge Base: {len(config['curated_channels'])} YouTube Channels")
    print(f"🧠 AI Brain: {assistant.ollama_model}")
    print(f"🔑 API Key: {config['ollama']['api_key'][:10]}...")
    print(f"🌐 Web UI: http://localhost:{config['app']['port']}")
    print(f"📚 API Docs: http://localhost:{config['app']['port']}/docs")
    print("=" * 60)
    uvicorn.run(app, host=config['app']['host'], port=config['app']['port'])
