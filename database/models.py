"""
SQLAlchemy Database Models for Munch AI Dating Assistant
Implements full schema from Munch AI Integration Action Plan
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

Base = declarative_base()

# ===================== ENUMS =====================

class ConversationStatus(str, Enum):
    """Conversation status types"""
    ACTIVE = "active"
    STALLED = "stalled"
    GHOSTED = "ghosted"
    SUCCESS = "success"

class ResponseType(str, Enum):
    """Context types for AI response generation"""
    DATING_APP = "Dating App"
    TEXT = "Text"
    DMS = "DMs"
    COLD_APPROACH = "Cold Approach"
    LIVE_DATING = "Live Dating"
    OPENERS = "Openers / Closers"
    PRACTICE = "Practice"

class MessageRole(str, Enum):
    """Message sender role"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

# ===================== MODELS =====================

class User(Base):
    """User account model"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    subscription_tier = Column(String(50), default='free', nullable=False)
    is_active = Column(Integer, default=1, nullable=False)  # 1 = active, 0 = disabled
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tier={self.subscription_tier})>"

class Conversation(Base):
    """Conversation tracking model"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False, index=True)
    response_type = Column(SQLEnum(ResponseType), nullable=False)
    chemistry_score = Column(Integer, default=0, nullable=False)
    success_rate = Column(Float, default=0.0, nullable=False)
    failure_rate = Column(Float, default=0.0, nullable=False)
    total_messages = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    last_message_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="conversation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversations_user_status', 'user_id', 'status'),
        Index('idx_conversations_updated_at', 'updated_at'),
    )
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, name={self.name}, status={self.status})>"

class Message(Base):
    """Individual message model"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index('idx_messages_conversation_created', 'conversation_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conv_id={self.conversation_id})>"

class Analytics(Base):
    """Analytics and tracking model"""
    __tablename__ = 'analytics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    chemistry_score = Column(Integer, nullable=False)
    success_rate = Column(Float, nullable=False)
    failure_rate = Column(Float, nullable=False)
    ai_tip = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="analytics")
    
    # Indexes
    __table_args__ = (
        Index('idx_analytics_conversation_analyzed', 'conversation_id', 'analyzed_at'),
    )
    
    def __repr__(self):
        return f"<Analytics(id={self.id}, conv_id={self.conversation_id}, chemistry={self.chemistry_score})>"
