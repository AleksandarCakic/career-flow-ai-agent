"""Tests for analytics service."""
import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from src.database import Base
from src.models import User, Conversation, Message, ConversationStatus, MessageRole
from src.services.analytics_service import AnalyticsService


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def analytics_service():
    """Create analytics service instance."""
    return AnalyticsService()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        phone_number="+15551234567",
        created_at=datetime.now(UTC)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_get_or_create_user_new(db_session, analytics_service):
    """Test creating a new user."""
    phone_number = "+15559876543"
    
    user = analytics_service.get_or_create_user(db_session, phone_number)
    
    assert user.phone_number == phone_number
    assert user.id is not None
    assert user.created_at is not None


def test_get_or_create_user_existing(db_session, analytics_service, test_user):
    """Test getting an existing user."""
    user = analytics_service.get_or_create_user(db_session, test_user.phone_number)
    
    assert user.id == test_user.id
    assert user.phone_number == test_user.phone_number


def test_create_conversation(db_session, analytics_service):
    """Test creating a new conversation."""
    call_sid = "CA123456"
    phone_number = "+15551234567"
    
    conversation = analytics_service.create_conversation(db_session, call_sid, phone_number)
    
    assert conversation.call_sid == call_sid
    assert conversation.phone_number == phone_number
    assert conversation.status == ConversationStatus.ACTIVE
    assert conversation.user_id is not None
    
    # Verify user was created
    user = db_session.query(User).filter(User.phone_number == phone_number).first()
    assert user is not None
    assert conversation.user_id == user.id


def test_create_conversation_existing_user(db_session, analytics_service, test_user):
    """Test creating conversation for existing user."""
    call_sid = "CA789012"
    
    conversation = analytics_service.create_conversation(
        db_session, 
        call_sid, 
        test_user.phone_number
    )
    
    assert conversation.user_id == test_user.id
    assert conversation.phone_number == test_user.phone_number


def test_log_message(db_session, analytics_service):
    """Test logging a message."""
    conversation = analytics_service.create_conversation(db_session, "CA123", "+15551234567")
    
    message = analytics_service.log_message(
        db_session,
        conversation.id,
        MessageRole.USER,
        "Hello, I need help"
    )
    
    assert message.conversation_id == conversation.id
    assert message.role == MessageRole.USER
    assert message.content == "Hello, I need help"
    assert message.timestamp is not None


def test_log_message_with_string_id(db_session, analytics_service):
    """Test logging message with string conversation_id."""
    conversation = analytics_service.create_conversation(db_session, "CA456", "+15551234567")
    
    message = analytics_service.log_message(
        db_session,
        str(conversation.id),
        MessageRole.ASSISTANT,
        "I can help you with that"
    )
    
    assert message.conversation_id == conversation.id


def test_get_conversation_by_call_sid(db_session, analytics_service):
    """Test retrieving conversation by call SID."""
    call_sid = "CA789"
    conversation = analytics_service.create_conversation(db_session, call_sid, "+15551234567")
    
    retrieved = analytics_service.get_conversation_by_call_sid(db_session, call_sid)
    
    assert retrieved is not None
    assert retrieved.id == conversation.id
    assert retrieved.call_sid == call_sid


def test_get_conversation_by_call_sid_not_found(db_session, analytics_service):
    """Test retrieving non-existent conversation."""
    result = analytics_service.get_conversation_by_call_sid(db_session, "CA999")
    assert result is None


def test_end_conversation(db_session, analytics_service):
    """Test ending a conversation."""
    conversation = analytics_service.create_conversation(db_session, "CA111", "+15551234567")
    
    ended = analytics_service.end_conversation(db_session, "CA111")
    
    assert ended is not None
    assert ended.status == ConversationStatus.COMPLETED
    assert ended.ended_at is not None
    assert ended.duration_seconds is not None


def test_end_conversation_with_status(db_session, analytics_service):
    """Test ending conversation with specific status."""
    conversation = analytics_service.create_conversation(db_session, "CA222", "+15551234567")
    
    ended = analytics_service.end_conversation(
        db_session, 
        "CA222", 
        ConversationStatus.FAILED
    )
    
    assert ended.status == ConversationStatus.FAILED


def test_get_all_conversations(db_session, analytics_service):
    """Test getting all conversations."""
    analytics_service.create_conversation(db_session, "CA001", "+15551111111")
    analytics_service.create_conversation(db_session, "CA002", "+15552222222")
    analytics_service.create_conversation(db_session, "CA003", "+15553333333")
    
    conversations = analytics_service.get_all_conversations(db_session)
    
    assert len(conversations) == 3


def test_get_all_conversations_pagination(db_session, analytics_service):
    """Test pagination of conversations."""
    for i in range(5):
        analytics_service.create_conversation(db_session, f"CA{i:03d}", "+15551234567")
    
    page1 = analytics_service.get_all_conversations(db_session, skip=0, limit=2)
    page2 = analytics_service.get_all_conversations(db_session, skip=2, limit=2)
    
    assert len(page1) == 2
    assert len(page2) == 2
    assert page1[0].id != page2[0].id


def test_conversation_duration_calculation(db_session, analytics_service):
    """Test that conversation duration is calculated correctly."""
    conversation = analytics_service.create_conversation(db_session, "CA333", "+15551234567")
    
    # Manually set started_at to 60 seconds ago
    setattr(conversation, 'started_at', datetime.now(UTC) - timedelta(seconds=60))
    db_session.commit()
    
    ended = analytics_service.end_conversation(db_session, "CA333")
    
    assert ended.duration_seconds is not None
    assert 59 <= ended.duration_seconds <= 61  # Allow 1 second margin


def test_get_user_conversations(db_session, analytics_service, test_user):
    """Test getting all conversations for a specific user."""
    # Create 3 conversations for test user
    analytics_service.create_conversation(db_session, "CA001", test_user.phone_number)
    analytics_service.create_conversation(db_session, "CA002", test_user.phone_number)
    analytics_service.create_conversation(db_session, "CA003", test_user.phone_number)
    
    # Create 1 conversation for different user
    analytics_service.create_conversation(db_session, "CA004", "+15559999999")
    
    conversations = analytics_service.get_user_conversations(db_session, test_user.id)
    
    assert len(conversations) == 3
    assert all(c.user_id == test_user.id for c in conversations)


def test_get_conversations_by_phone(db_session, analytics_service):
    """Test getting conversations by phone number."""
    phone = "+15551234567"
    
    analytics_service.create_conversation(db_session, "CA001", phone)
    analytics_service.create_conversation(db_session, "CA002", phone)
    analytics_service.create_conversation(db_session, "CA003", "+15559999999")
    
    conversations = analytics_service.get_conversations_by_phone(db_session, phone)
    
    assert len(conversations) == 2
    assert all(c.phone_number == phone for c in conversations)


def test_get_conversations_by_phone_no_user(db_session, analytics_service):
    """Test getting conversations for non-existent phone."""
    conversations = analytics_service.get_conversations_by_phone(
        db_session, 
        "+15559999999"
    )
    
    assert len(conversations) == 0


def test_get_user_by_phone(db_session, analytics_service, test_user):
    """Test getting user by phone number."""
    user = analytics_service.get_user_by_phone(db_session, test_user.phone_number)
    
    assert user is not None
    assert user.id == test_user.id


def test_get_user_by_phone_not_found(db_session, analytics_service):
    """Test getting non-existent user."""
    user = analytics_service.get_user_by_phone(db_session, "+15559999999")
    assert user is None


def test_get_stats_empty(db_session, analytics_service):
    """Test stats with no data."""
    stats = analytics_service.get_stats(db_session)
    
    assert stats["total_users"] == 0
    assert stats["total_conversations"] == 0
    assert stats["total_messages"] == 0


def test_get_stats_with_data(db_session, analytics_service):
    """Test stats with data."""
    # Create 2 users with conversations
    conv1 = analytics_service.create_conversation(db_session, "CA001", "+15551111111")
    conv2 = analytics_service.create_conversation(db_session, "CA002", "+15552222222")
    conv3 = analytics_service.create_conversation(db_session, "CA003", "+15551111111")
    
    # Add messages
    analytics_service.log_message(db_session, conv1.id, MessageRole.USER, "Test 1")
    analytics_service.log_message(db_session, conv1.id, MessageRole.ASSISTANT, "Reply 1")
    analytics_service.log_message(db_session, conv2.id, MessageRole.USER, "Test 2")
    
    # End one conversation
    analytics_service.end_conversation(db_session, "CA001")
    
    stats = analytics_service.get_stats(db_session)
    
    assert stats["total_users"] == 2
    assert stats["total_conversations"] == 3
    assert stats["active_conversations"] == 2
    assert stats["completed_conversations"] == 1
    assert stats["total_messages"] == 3
    assert stats["average_messages_per_conversation"] == 1.0


def test_update_user_last_call_at(db_session, analytics_service, test_user):
    """Test that last_call_at is updated on new conversation."""
    original_last_call = test_user.last_call_at
    
    # Create new conversation
    analytics_service.create_conversation(db_session, "CA999", test_user.phone_number)
    
    # Refresh user
    db_session.refresh(test_user)
    
    assert test_user.last_call_at is not None
    if original_last_call:
        assert test_user.last_call_at > original_last_call


def test_user_data_field(db_session):
    """Test storing user data (renamed from metadata)."""
    user = User(
        id=uuid.uuid4(),
        phone_number="+15551234568",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        user_data={"career_goal": "Software Engineer", "experience_years": 5}
    )
    
    db_session.add(user)
    db_session.commit()
    
    retrieved = db_session.query(User).filter(User.phone_number == "+15551234568").first()
    assert retrieved.first_name == "John"
    assert retrieved.user_data["career_goal"] == "Software Engineer"