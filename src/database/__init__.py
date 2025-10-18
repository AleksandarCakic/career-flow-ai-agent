"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import settings

# Create declarative base
Base = declarative_base()

# Create engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Alias for backwards compatibility
get_db = get_db_session


def init_db():
    """Initialize database tables."""
    # Import all models to ensure they're registered with Base
    from src.models import models  # Updated import
    Base.metadata.create_all(bind=engine)


# Export Base for use in models
__all__ = ["Base", "engine", "SessionLocal", "get_db_session", "get_db", "init_db"]