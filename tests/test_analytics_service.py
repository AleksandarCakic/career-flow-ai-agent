"""Tests for analytics service."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.models.base import Base
from src.models.conversation import Conversation, Message, ConversationStatus, MessageRole
from src.services.analytics_service import AnalyticsService


# Create in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_conversation(db_session: Session):
    """Test creating a conversation."""
    analytics = AnalyticsService()
    
    conversation = analytics.create_conversation(
        db_session,
        call_sid="CA123456",
        phone_number="+15551234567"
    )
    
    assert conversation.call_sid == "CA123456"
    assert conversation.phone_number == "+15551234567"
    assert conversation.status == ConversationStatus.ACTIVE
    assert conversation.started_at is not None

def test_end_conversation(db_session: Session):
    """Test ending a conversation."""
    analytics = AnalyticsService()
    
    # Create conversation
    conversation = analytics.create_conversation(
        db_session,
        call_sid="CA123456",
        phone_number="+15551234567"
    )
    
    # End conversation
    ended_conv = analytics.end_conversation(
        db_session,
        call_sid="CA123456",
        status=ConversationStatus.COMPLETED
    )
    
    assert ended_conv is not None
    assert ended_conv.status == ConversationStatus.COMPLETED
    assert ended_conv.ended_at is not None
    assert ended_conv.duration_seconds is not None


def test_get_conversation_by_call_sid(db_session: Session):
    """Test retrieving conversation by call SID."""
    analytics = AnalyticsService()
    
    # Create conversation
    created_conv = analytics.create_conversation(
        db_session,
        call_sid="CA123456",
        phone_number="+15551234567"
    )
    
    # Retrieve it
    retrieved_conv = analytics.get_conversation_by_call_sid(
        db_session,
        call_sid="CA123456"
    )
    
    assert retrieved_conv is not None
    assert retrieved_conv.call_sid == "CA123456"


def test_get_all_conversations(db_session: Session):
    """Test retrieving all conversations."""
    analytics = AnalyticsService()
    
    # Create multiple conversations
    analytics.create_conversation(db_session, "CA111", "+15551111111")
    analytics.create_conversation(db_session, "CA222", "+15552222222")
    analytics.create_conversation(db_session, "CA333", "+15553333333")
    
    # Retrieve all
    conversations = analytics.get_all_conversations(db_session, limit=10)
    
    assert len(conversations) == 3


def test_conversation_duration_calculation(db_session: Session):
    """Test that duration is calculated correctly."""
    analytics = AnalyticsService()
    
    # Create conversation
    conversation = analytics.create_conversation(
        db_session,
        call_sid="CA123456",
        phone_number="+15551234567"
    )
    
    # Manually set started_at to 1 minute ago for testing
    conversation.started_at = datetime.utcnow() - timedelta(minutes=1)
    db_session.commit()
    
    # End conversation
    ended_conv = analytics.end_conversation(
        db_session,
        call_sid="CA123456"
    )
    
    assert ended_conv.duration_seconds is not None
    assert ended_conv.duration_seconds >= 55  # Should be ~60 seconds
    assert ended_conv.duration_seconds <= 65