"""
Database Engine and Session Management
Handles database connections and session lifecycle
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./munch_ai.db")

# Create engine
# For SQLite: add connect_args for thread safety
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False  # Set to True for SQL query logging
    )
else:
    # For PostgreSQL
    engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ===================== DATABASE UTILITIES =====================

def init_db():
    """Initialize database - create all tables"""
    from database.models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")

def get_db() -> Session:
    """
    Dependency for FastAPI endpoints
    Usage: def endpoint(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """
    Context manager for manual database operations
    Usage: 
        with get_db_session() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def drop_all_tables():
    """⚠️ WARNING: Drops all tables - use only in development"""
    from database.models import Base
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All tables dropped!")

def reset_db():
    """⚠️ WARNING: Drops and recreates all tables - development only"""
    drop_all_tables()
    init_db()
    print("✅ Database reset complete!")
