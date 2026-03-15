"""
Database package for Munch AI Dating Assistant
Exports models, engine, and session utilities
"""
from database.models import (
    Base,
    User,
    Conversation,
    Message,
    Analytics,
    ConversationStatus,
    ResponseType,
    MessageRole
)
from database.database import (
    engine,
    SessionLocal,
    get_db,
    get_db_session,
    init_db,
    reset_db
)

__all__ = [
    # Models
    'Base',
    'User',
    'Conversation',
    'Message',
    'Analytics',
    # Enums
    'ConversationStatus',
    'ResponseType',
    'MessageRole',
    # Database utilities
    'engine',
    'SessionLocal',
    'get_db',
    'get_db_session',
    'init_db',
    'reset_db'
]
