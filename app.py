#!/usr/bin/env python3
"""
Dating AI Assistant - FINAL COMPLETE VERSION
Cloud-Powered with Ollama & YouTube Knowledge Base
Database-backed conversation tracking and analytics
"""
from fastapi import FastAPI, HTTPException, Depends, Query, Header, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import yaml
import os
import requests
import json
from datetime import datetime

# Sentry Error Tracking
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% of transactions for performance
            profiles_sample_rate=0.1,
            environment=os.getenv("ENVIRONMENT", "development"),
            release=os.getenv("APP_VERSION", "5.0.0"),
        )
        print("   Sentry error tracking enabled")
    except ImportError:
        print("   sentry-sdk not installed. Error tracking disabled.")

# Database imports
from database import init_db, get_db
from database.models import (
    ConversationStatus, ResponseType, MessageRole
)
from services.database_service import DatabaseService, get_database_service
from services.analysis_service import AnalysisService, get_analysis_service
from services.auth_service import (
    AuthService, get_auth_service, Token, AuthResult,
    verify_token, TokenPayload
)
from services.image_service import ImageAnalysisService, get_image_service
from services.cache_service import CacheService, get_cache_service

# Security
security = HTTPBearer(auto_error=False)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)

# ===================== FASTAPI APP SETUP =====================
app = FastAPI(title="Munch - AI Dating Assistant", version="5.0.0")

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

# New models for conversation management
class UserCreate(BaseModel):
    email: str
    username: Optional[str] = None
    subscription_tier: str = "free"

class UserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str]
    subscription_tier: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    user_id: int
    name: str
    response_type: str = Field(..., description="One of: Dating App, Text, DMs, Cold Approach, Live Dating, Openers / Closers, Practice")

class ConversationUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    chemistry_score: Optional[int] = None
    success_rate: Optional[float] = None
    failure_rate: Optional[float] = None

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    name: str
    status: str
    response_type: str
    chemistry_score: int
    success_rate: float
    failure_rate: float
    total_messages: int
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    role: str = Field(..., description="One of: user, assistant, system")
    content: str
    image_url: Optional[str] = None

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    image_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    id: int
    conversation_id: int
    chemistry_score: int
    success_rate: float
    failure_rate: float
    ai_tip: Optional[str]
    analyzed_at: datetime

    class Config:
        from_attributes = True

class AISuggestionRequest(BaseModel):
    conversation_id: int
    context_type: Optional[str] = None


# Auth models
class AuthRegister(BaseModel):
    email: str
    password: str
    username: Optional[str] = None
    subscription_tier: str = "free"


class AuthLogin(BaseModel):
    email: str
    password: str


class AuthRefresh(BaseModel):
    refresh_token: str


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


# Image analysis models
class ImageAnalyzeBase64(BaseModel):
    image_base64: str
    conversation_id: Optional[int] = None  # Optional: auto-add extracted messages

# ===================== LOAD CONFIG =====================
with open("config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

# ===================== AI ASSISTANT CORE =====================
class DatingAssistant:
    def __init__(self):
        # Ollama Desktop App configuration (routes to cloud models)
        self.base_url = config['ollama'].get('base_url', 'http://localhost:11434')
        self.primary_model = config['ollama'].get('primary_model', 'gpt-oss:20b-cloud')
        self.fallback_models = config['ollama'].get('fallback_models', ['glm-4:6b-cloud', 'minimax-m2-cloud'])
        self.ollama_model = config['ollama'].get('cloud_model', self.primary_model)

        # Current active model
        self.active_model = self.primary_model

        print(f"✅ Assistant initialized with Ollama Desktop (Cloud Models)")
        print(f"   Primary: {self.primary_model}")
        print(f"   Fallbacks: {', '.join(self.fallback_models)}")

        # Test connection and find available model
        if self._test_connection():
            available_model = self._find_available_model()
            if available_model:
                self.active_model = available_model
                print(f"   🔗 Connected! Using: {self.active_model}")
            else:
                print(f"   🔗 Connected! Will use: {self.primary_model}")
        else:
            print("   ⚠️  Ollama not running. Start Ollama Desktop app first.")

        self.interest_thresholds = {'high': 70, 'medium': 40, 'low': 0}
        self.reply_timing = {'high': "15-45 min", 'medium': "1-3 hours", 'low': "4-24 hours"}

    def _find_available_model(self) -> Optional[str]:
        """Find first available model from primary + fallbacks"""
        models_to_try = [self.primary_model] + self.fallback_models

        for model in models_to_try:
            if self._test_model(model):
                return model
        return None

    def _test_model(self, model: str) -> bool:
        """Test if a specific model is available"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": model, "prompt": "Hi", "stream": False},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False

    def _test_connection(self) -> bool:
        """Test if we can reach local Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _call_ollama(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        """Core function to call local Ollama API with fallback support"""
        model = model or self.active_model
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.7}
        }

        # Try primary model first, then fallbacks
        models_to_try = [model] + [m for m in self.fallback_models if m != model]

        for try_model in models_to_try:
            try:
                payload["model"] = try_model
                response = requests.post(url, json=payload, timeout=90)
                response.raise_for_status()
                result = response.json()

                # Update active model if fallback succeeded
                if try_model != self.active_model:
                    print(f"   Switched to fallback model: {try_model}")
                    self.active_model = try_model

                return result['message']['content']
            except Exception as e:
                print(f"   Model {try_model} failed: {e}")
                continue

        return "I apologize, but I'm having trouble connecting to the AI brain right now. Please check that Ollama is running."

    def _call_ollama_cloud(self, system_prompt: str, user_prompt: str) -> str:
        """Wrapper for backward compatibility - uses local Ollama"""
        return self._call_ollama(system_prompt, user_prompt)
    
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
            advice = "She's into it. Time to close - propose a specific time and place. Lead, don't ask."
        elif score >= 40:
            level = "medium"
            advice = "Building momentum. Stay playful, create some mystery, don't over-invest."
        else:
            level = "low"
            advice = "Interest is low. Either spark something fun or pull back and refocus."
        return {
            "score": score,
            "level": level,
            "advice": advice,
            "reply_time": self.reply_timing[level],
            "analyzed_messages": len(recent_msgs)
        }
    
    def generate_advice(self, query: str, context: List[str] = []) -> dict:
        """Generate dating advice using psychology from your YouTube channels"""
        system_prompt = """You are an elite dating coach who understands the balance between confidence and charm.

YOUR STYLE:
- Confident but not robotic. You have personality.
- Direct when it matters, playful when appropriate.
- You understand that attraction is built through humor, mystery, and tension.
- You know when to push forward and when to pull back.
- You give advice that sounds natural, not scripted.

PRINCIPLES:
- Confidence is attractive, but so is being fun to talk to.
- Leading the interaction doesn't mean being a drill sergeant.
- The best game feels effortless - like you're just naturally charming.
- Read the situation - playful banter needs playful responses, logistics need clarity.
- Keep some mystery. Don't over-explain everything."""
        youtube_context = " | ".join(context) if context else "General dating psychology principles"
        user_prompt = f"""SITUATION: {query}

Give practical advice that balances confidence with charm. Be direct but not robotic."""
        advice = self._call_ollama_cloud(system_prompt, user_prompt)
        return {
            "response": advice,
            "sources": youtube_context,
            "model": self.ollama_model,
            "premium_insight": "Use 'push-pull' and qualification techniques." if len(context) > 2 else None
        }
    
    def generate_premium_opener(self, profile_context: str = "", platform: str = "instagram") -> dict:
        """Generate unforgettable opening lines"""
        system_prompt = f"""You write {platform} openers that are intriguing and fun.

THE GOAL:
- Make her curious enough to respond.
- Stand out from "hey" and "you're beautiful".
- Show personality - confident but not aggressive.

GOOD OPENERS:
- Playful observations or cold reads about her.
- Witty comments that invite banter.
- Confident but charming - you're fun, not intimidating.
- Specific to her if you have context. Generic = ignored.

AVOID:
- Interview questions ("what do you do?")
- Generic compliments ("you're gorgeous")
- Try-hard edginess
- Anything that sounds copy-pasted"""
        user_prompt = f"Write ONE opener that's confident and intriguing."
        if profile_context:
            user_prompt += f"\nHer profile: '{profile_context}'"
        user_prompt += "\n\nOPENER (just the line, nothing else):"
        opener = self._call_ollama_cloud(system_prompt, user_prompt)
        return {
            "opener": opener,
            "technique": "Cold Read + Qualification + Open Loop",
            "platform": platform,
            "success_rate": "72-85% expected response"
        }

# ===================== INITIALIZE ASSISTANT =====================
assistant = DatingAssistant()

# Initialize Analysis Service (Ollama Desktop -> Cloud Models)
analysis_service = get_analysis_service(
    ollama_model=config['ollama'].get('primary_model', 'gpt-oss:20b-cloud'),
    base_url=config['ollama'].get('base_url', 'http://localhost:11434'),
    fallback_models=config['ollama'].get('fallback_models', ['glm-4:6b-cloud', 'minimax-m2-cloud'])
)

# Initialize Auth Service
auth_service = get_auth_service()

# Initialize Image Service (using Gemini which has vision capability)
image_service = get_image_service(
    base_url=config['ollama'].get('base_url', 'http://localhost:11434'),
    model="gemini-3-flash-preview:cloud",  # Has vision capability
    fallback_models=[]
)

# Initialize Cache Service
cache_service = get_cache_service()


# ===================== AUTHENTICATION DEPENDENCIES =====================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """
    Dependency to get the current authenticated user from JWT token.
    Raises HTTPException if token is invalid or missing.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return payload


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[TokenPayload]:
    """
    Optional authentication - returns None if no token provided.
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    return verify_token(token, token_type="access")

# ===================== INITIALIZE DATABASE =====================
@app.on_event("startup")
async def startup_event():
    """Initialize database on app startup"""
    init_db()
    print("Database initialized successfully!")

# ===================== STATIC FILES =====================
app.mount("/static", StaticFiles(directory="web_interface"), name="static")

@app.get("/")
async def root():
    return FileResponse("web_interface/index.html")

# ===================== API ROUTES =====================
@app.get("/api")
async def api_root():
    return {
        "message": "Munch - AI Dating Assistant API",
        "version": "5.0.0",
        "model": config['ollama']['cloud_model'],
        "endpoints": {
            "health": "GET /health - Health check",
            "advice": "POST /advice - Get dating advice",
            "analyze": "POST /analyze - Analyze interest level",
            "opener": "POST /opener - Generate premium opener",
            "auth": {
                "register": "POST /api/auth/register - Register new user",
                "login": "POST /api/auth/login - Login with email/password",
                "refresh": "POST /api/auth/refresh - Refresh access token",
                "change_password": "POST /api/auth/change-password - Change password (auth required)",
                "me": "GET /api/auth/me - Get current user info (auth required)"
            },
            "users": {
                "create": "POST /api/users - Create user",
                "get": "GET /api/users/{email} - Get user by email"
            },
            "conversations": {
                "create": "POST /api/conversations - Create conversation",
                "list": "GET /api/conversations?user_id={id} - List conversations",
                "get": "GET /api/conversations/{id} - Get conversation",
                "update": "PUT /api/conversations/{id} - Update conversation",
                "delete": "DELETE /api/conversations/{id} - Delete conversation",
                "messages": {
                    "add": "POST /api/conversations/{id}/messages - Add message",
                    "list": "GET /api/conversations/{id}/messages - Get messages"
                },
                "analyze": "POST /api/conversations/{id}/analyze - Analyze conversation"
            },
            "stats": "GET /api/users/{user_id}/stats - Get user statistics"
        },
        "docs": "/docs",
        "web_ui": "/"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model": config['ollama']['cloud_model'],
        "cache": "connected" if cache_service.available else "unavailable"
    }

@app.post("/advice")
@limiter.limit("10/minute")
async def get_advice(request: Request, message_request: MessageRequest):
    result = assistant.generate_advice(message_request.text, message_request.context)
    return {"success": True, "data": result, "premium": message_request.user_type == "premium"}

@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze_interest(request: Request, interest_request: InterestAnalysis):
    analysis = assistant.analyze_interest(interest_request.messages)
    return {"success": True, "analysis": analysis}

@app.post("/opener")
@limiter.limit("10/minute")
async def get_opener(request: Request, opener_request: OpenerRequest):
    opener = assistant.generate_premium_opener(opener_request.profile_context, opener_request.platform)
    return {"success": True, "opener": opener}


# ===================== AUTHENTICATION ENDPOINTS =====================

@app.post("/api/auth/register")
@limiter.limit("5/minute")
async def register(request: Request, auth_data: AuthRegister):
    """
    Register a new user with email and password.
    Returns JWT tokens on success.
    """
    result = auth_service.register_user(
        email=auth_data.email,
        password=auth_data.password,
        username=auth_data.username,
        subscription_tier=auth_data.subscription_tier
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return {
        "success": True,
        "message": result.message,
        "user_id": result.user_id,
        "token": {
            "access_token": result.token.access_token,
            "refresh_token": result.token.refresh_token,
            "token_type": result.token.token_type,
            "expires_in": result.token.expires_in
        }
    }


@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, auth_data: AuthLogin):
    """
    Authenticate user with email and password.
    Returns JWT tokens on success.
    """
    result = auth_service.login(
        email=auth_data.email,
        password=auth_data.password
    )

    if not result.success:
        raise HTTPException(status_code=401, detail=result.message)

    return {
        "success": True,
        "message": result.message,
        "user_id": result.user_id,
        "token": {
            "access_token": result.token.access_token,
            "refresh_token": result.token.refresh_token,
            "token_type": result.token.token_type,
            "expires_in": result.token.expires_in
        }
    }


@app.post("/api/auth/refresh")
async def refresh_token(refresh_data: AuthRefresh):
    """
    Refresh access token using refresh token.
    Returns new JWT tokens on success.
    """
    result = auth_service.refresh(refresh_data.refresh_token)

    if not result.success:
        raise HTTPException(status_code=401, detail=result.message)

    return {
        "success": True,
        "message": result.message,
        "token": {
            "access_token": result.token.access_token,
            "refresh_token": result.token.refresh_token,
            "token_type": result.token.token_type,
            "expires_in": result.token.expires_in
        }
    }


@app.post("/api/auth/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Change password for authenticated user.
    Requires valid access token.
    """
    result = auth_service.change_password(
        user_id=current_user.user_id,
        old_password=password_data.old_password,
        new_password=password_data.new_password
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return {
        "success": True,
        "message": result.message
    }


@app.get("/api/auth/me")
async def get_current_user_info(
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    Requires valid access token.
    """
    db_service = get_database_service()
    user = db_service.get_user_by_id(current_user.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "subscription_tier": user.subscription_tier,
            "created_at": user.created_at.isoformat()
        }
    }


# ===================== USER ENDPOINTS =====================
@app.post("/api/users", response_model=dict)
async def create_user(user: UserCreate):
    """Create a new user"""
    db_service = get_database_service()
    try:
        new_user, created = db_service.get_or_create_user(
            email=user.email,
            username=user.username,
            subscription_tier=user.subscription_tier
        )
        return {
            "success": True,
            "created": created,
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "username": new_user.username,
                "subscription_tier": new_user.subscription_tier,
                "created_at": new_user.created_at.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/users/{email}")
async def get_user(email: str):
    """Get user by email"""
    db_service = get_database_service()
    user = db_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "subscription_tier": user.subscription_tier,
            "created_at": user.created_at.isoformat()
        }
    }

@app.get("/api/users/{user_id}/stats")
async def get_user_stats(user_id: int):
    """Get user statistics (cached)"""
    # Try cache first
    cached = cache_service.get_user_stats(user_id)
    if cached:
        return {"success": True, "stats": cached, "cached": True}

    db_service = get_database_service()
    user = db_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    stats = db_service.get_user_stats(user_id)

    # Cache for 2 minutes
    cache_service.set_user_stats(user_id, stats, ttl=120)

    return {"success": True, "stats": stats, "cached": False}

# ===================== CONVERSATION ENDPOINTS =====================
def _parse_response_type(response_type_str: str) -> ResponseType:
    """Convert string to ResponseType enum"""
    type_map = {
        "dating app": ResponseType.DATING_APP,
        "text": ResponseType.TEXT,
        "dms": ResponseType.DMS,
        "cold approach": ResponseType.COLD_APPROACH,
        "live dating": ResponseType.LIVE_DATING,
        "openers / closers": ResponseType.OPENERS,
        "openers": ResponseType.OPENERS,
        "closers": ResponseType.OPENERS,
        "practice": ResponseType.PRACTICE
    }
    return type_map.get(response_type_str.lower(), ResponseType.DATING_APP)

def _parse_conversation_status(status_str: str) -> ConversationStatus:
    """Convert string to ConversationStatus enum"""
    status_map = {
        "active": ConversationStatus.ACTIVE,
        "stalled": ConversationStatus.STALLED,
        "ghosted": ConversationStatus.GHOSTED,
        "success": ConversationStatus.SUCCESS
    }
    return status_map.get(status_str.lower(), ConversationStatus.ACTIVE)

def _parse_message_role(role_str: str) -> MessageRole:
    """Convert string to MessageRole enum"""
    role_map = {
        "user": MessageRole.USER,
        "assistant": MessageRole.ASSISTANT,
        "system": MessageRole.SYSTEM
    }
    return role_map.get(role_str.lower(), MessageRole.USER)

@app.post("/api/conversations")
async def create_conversation(conv: ConversationCreate):
    """Create a new conversation"""
    db_service = get_database_service()

    # Verify user exists
    user = db_service.get_user_by_id(conv.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    response_type = _parse_response_type(conv.response_type)
    conversation = db_service.create_conversation(
        user_id=conv.user_id,
        name=conv.name,
        response_type=response_type
    )
    return {
        "success": True,
        "conversation": {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "name": conversation.name,
            "status": conversation.status.value,
            "response_type": conversation.response_type.value,
            "chemistry_score": conversation.chemistry_score,
            "total_messages": conversation.total_messages,
            "created_at": conversation.created_at.isoformat()
        }
    }

@app.get("/api/conversations")
async def list_conversations(
    user_id: int = Query(..., description="User ID to filter conversations"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List conversations for a user"""
    db_service = get_database_service()

    status_enum = _parse_conversation_status(status) if status else None
    conversations = db_service.get_conversations_by_user(
        user_id=user_id,
        status=status_enum,
        limit=limit,
        offset=offset
    )

    return {
        "success": True,
        "count": len(conversations),
        "conversations": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status.value,
                "response_type": c.response_type.value,
                "chemistry_score": c.chemistry_score,
                "success_rate": c.success_rate,
                "failure_rate": c.failure_rate,
                "total_messages": c.total_messages,
                "updated_at": c.updated_at.isoformat(),
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None
            }
            for c in conversations
        ]
    }

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: int):
    """Get conversation details with messages"""
    db_service = get_database_service()

    result = db_service.get_conversation_with_messages(conversation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = result["conversation"]
    messages = result["messages"]

    return {
        "success": True,
        "conversation": {
            "id": conv.id,
            "user_id": conv.user_id,
            "name": conv.name,
            "status": conv.status.value,
            "response_type": conv.response_type.value,
            "chemistry_score": conv.chemistry_score,
            "success_rate": conv.success_rate,
            "failure_rate": conv.failure_rate,
            "total_messages": conv.total_messages,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat()
        },
        "messages": [
            {
                "id": m.id,
                "role": m.role.value,
                "content": m.content,
                "image_url": m.image_url,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    }

@app.put("/api/conversations/{conversation_id}")
async def update_conversation(conversation_id: int, update: ConversationUpdate):
    """Update conversation details"""
    db_service = get_database_service()

    status_enum = _parse_conversation_status(update.status) if update.status else None

    conversation = db_service.update_conversation(
        conversation_id=conversation_id,
        name=update.name,
        status=status_enum,
        chemistry_score=update.chemistry_score,
        success_rate=update.success_rate,
        failure_rate=update.failure_rate
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "success": True,
        "conversation": {
            "id": conversation.id,
            "name": conversation.name,
            "status": conversation.status.value,
            "chemistry_score": conversation.chemistry_score,
            "success_rate": conversation.success_rate,
            "failure_rate": conversation.failure_rate,
            "updated_at": conversation.updated_at.isoformat()
        }
    }

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """Delete a conversation and all its messages"""
    db_service = get_database_service()

    deleted = db_service.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"success": True, "message": "Conversation deleted"}

# ===================== MESSAGE ENDPOINTS =====================
@app.post("/api/conversations/{conversation_id}/messages")
async def add_message(conversation_id: int, message: MessageCreate):
    """Add a message to a conversation"""
    db_service = get_database_service()

    # Verify conversation exists
    conv = db_service.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    role = _parse_message_role(message.role)
    new_message = db_service.add_message(
        conversation_id=conversation_id,
        role=role,
        content=message.content,
        image_url=message.image_url
    )

    return {
        "success": True,
        "message": {
            "id": new_message.id,
            "conversation_id": new_message.conversation_id,
            "role": new_message.role.value,
            "content": new_message.content,
            "image_url": new_message.image_url,
            "created_at": new_message.created_at.isoformat()
        }
    }

@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get messages for a conversation"""
    db_service = get_database_service()

    messages = db_service.get_conversation_messages(
        conversation_id=conversation_id,
        limit=limit,
        offset=offset
    )

    return {
        "success": True,
        "count": len(messages),
        "messages": [
            {
                "id": m.id,
                "role": m.role.value,
                "content": m.content,
                "image_url": m.image_url,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    }

# ===================== CONVERSATION ANALYSIS ENDPOINTS =====================
@app.post("/api/conversations/{conversation_id}/analyze")
@limiter.limit("10/minute")
async def analyze_conversation(request: Request, conversation_id: int):
    """Analyze a conversation using advanced AI analysis"""
    db_service = get_database_service()

    # Get conversation with messages
    result = db_service.get_conversation_with_messages(conversation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = result["conversation"]
    messages = result["messages"]

    if not messages:
        return {
            "success": True,
            "analysis": {
                "chemistry_score": 50,
                "success_rate": 0,
                "failure_rate": 0,
                "status": conv.status.value,
                "ai_tip": "Add some messages to analyze!",
                "signals": []
            }
        }

    # Use advanced AnalysisService
    analysis = analysis_service.analyze_conversation(messages, conv.response_type)

    # Save analytics
    db_service.save_analytics(
        conversation_id=conversation_id,
        chemistry_score=analysis["chemistry_score"],
        success_rate=analysis["success_rate"],
        failure_rate=analysis["failure_rate"],
        ai_tip=analysis["ai_tip"]
    )

    # Update conversation status
    db_service.update_conversation(
        conversation_id=conversation_id,
        status=analysis["status"]
    )

    return {
        "success": True,
        "analysis": {
            "chemistry_score": analysis["chemistry_score"],
            "interest_level": analysis["interest_level"],
            "success_rate": analysis["success_rate"],
            "failure_rate": analysis["failure_rate"],
            "status": analysis["status"].value,
            "ai_tip": analysis["ai_tip"],
            "signals": analysis["signals"],
            "component_scores": analysis["component_scores"],
            "messages_analyzed": len(messages)
        }
    }

@app.post("/api/ai/suggest")
@limiter.limit("10/minute")
async def get_ai_suggestion(request: Request, suggestion_request: AISuggestionRequest):
    """Get AI-suggested response for a conversation"""
    db_service = get_database_service()

    result = db_service.get_conversation_with_messages(suggestion_request.conversation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = result["conversation"]
    messages = result["messages"]

    if not messages:
        return {
            "success": True,
            "suggestion": "Start the conversation with a confident, engaging opener!",
            "context_type": conv.response_type.value,
            "chemistry_score": 50
        }

    # Get current chemistry score
    analysis = analysis_service.analyze_conversation(messages, conv.response_type)

    # Generate AI suggestion using AnalysisService
    suggestion = analysis_service.generate_ai_response_suggestion(
        messages=messages,
        response_type=conv.response_type,
        chemistry_score=analysis["chemistry_score"]
    )

    return {
        "success": True,
        "suggestion": suggestion,
        "context_type": conv.response_type.value,
        "chemistry_score": analysis["chemistry_score"],
        "interest_level": analysis["interest_level"],
        "messages_analyzed": len(messages)
    }

@app.get("/api/conversations/{conversation_id}/analytics")
async def get_conversation_analytics(conversation_id: int):
    """Get analytics history for a conversation"""
    db_service = get_database_service()

    analytics = db_service.get_analytics_history(conversation_id)

    return {
        "success": True,
        "count": len(analytics),
        "analytics": [
            {
                "id": a.id,
                "chemistry_score": a.chemistry_score,
                "success_rate": a.success_rate,
                "failure_rate": a.failure_rate,
                "ai_tip": a.ai_tip,
                "analyzed_at": a.analyzed_at.isoformat()
            }
            for a in analytics
        ]
    }


@app.get("/api/conversations/{conversation_id}/progression")
async def get_conversation_progression(conversation_id: int):
    """Get chemistry score progression for a conversation over time"""
    db_service = get_database_service()

    # Verify conversation exists
    conv = db_service.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    progression = db_service.get_conversation_progression(conversation_id)
    return {"success": True, **progression}


# ===================== ANALYTICS TRENDS ENDPOINTS =====================

@app.get("/api/analytics/trends")
async def get_analytics_trends(
    user_id: int = Query(..., description="User ID to get trends for"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    granularity: str = Query("daily", description="Aggregation: 'daily' or 'weekly'")
):
    """
    Get aggregated analytics trends for a user over time.
    Shows chemistry score progression, success rates, and trend direction.
    """
    db_service = get_database_service()

    # Parse dates
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    if granularity not in ["daily", "weekly"]:
        raise HTTPException(status_code=400, detail="granularity must be 'daily' or 'weekly'")

    trends = db_service.get_analytics_trends(
        user_id=user_id,
        start_date=start_dt,
        end_date=end_dt,
        granularity=granularity
    )

    return {"success": True, **trends}


@app.get("/api/analytics/summary/{user_id}")
async def get_user_analytics_summary(user_id: int):
    """
    Get a comprehensive analytics summary for a user.
    Combines stats with trend data.
    """
    db_service = get_database_service()

    user = db_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stats = db_service.get_user_stats(user_id)
    trends = db_service.get_analytics_trends(user_id=user_id)

    return {
        "success": True,
        "user_id": user_id,
        "stats": stats,
        "trends": {
            "period": "last_30_days",
            "data_points": trends["data_points"][-7:],  # Last 7 data points
            "summary": trends["summary"]
        }
    }


# ===================== IMAGE ANALYSIS ENDPOINTS =====================

@app.post("/api/image/analyze")
@limiter.limit("5/minute")
async def analyze_image_base64(request: Request, image_data: ImageAnalyzeBase64):
    """
    Analyze a conversation screenshot from base64 encoded image.
    Extracts messages using vision AI and optionally adds them to a conversation.
    """
    result = image_service.analyze_base64_image(image_data.image_base64)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    response = {
        "success": True,
        "messages": [
            {
                "sender": m.sender,
                "content": m.content,
                "timestamp": m.timestamp
            }
            for m in result.messages
        ],
        "platform_detected": result.platform_detected,
        "message_count": len(result.messages)
    }

    # Optionally add messages to a conversation
    if image_data.conversation_id:
        db_service = get_database_service()
        conv = db_service.get_conversation(image_data.conversation_id)

        if conv:
            for msg in result.messages:
                role = MessageRole.USER if msg.sender == "user" else MessageRole.ASSISTANT
                db_service.add_message(
                    conversation_id=image_data.conversation_id,
                    role=role,
                    content=msg.content
                )
            response["added_to_conversation"] = image_data.conversation_id
            response["messages_added"] = len(result.messages)

    return response


@app.post("/api/image/upload")
@limiter.limit("5/minute")
async def analyze_image_upload(
    request: Request,
    file: UploadFile = File(...),
    conversation_id: Optional[int] = None
):
    """
    Analyze a conversation screenshot from file upload.
    Extracts messages using vision AI.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read file
    image_data = await file.read()

    # Validate image
    is_valid, info, error = image_service.validate_image(image_data)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Analyze
    result = image_service.analyze_image(image_data)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    response = {
        "success": True,
        "image_info": {
            "width": info.width,
            "height": info.height,
            "format": info.format,
            "size_bytes": info.size_bytes
        },
        "messages": [
            {
                "sender": m.sender,
                "content": m.content,
                "timestamp": m.timestamp
            }
            for m in result.messages
        ],
        "platform_detected": result.platform_detected,
        "message_count": len(result.messages)
    }

    # Optionally add messages to a conversation
    if conversation_id:
        db_service = get_database_service()
        conv = db_service.get_conversation(conversation_id)

        if conv:
            for msg in result.messages:
                role = MessageRole.USER if msg.sender == "user" else MessageRole.ASSISTANT
                db_service.add_message(
                    conversation_id=conversation_id,
                    role=role,
                    content=msg.content
                )
            response["added_to_conversation"] = conversation_id
            response["messages_added"] = len(result.messages)

    return response


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
