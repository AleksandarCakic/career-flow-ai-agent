"""Tests for conversation memory service."""
import pytest
from src.services.conversation_memory_service import ConversationMemoryService
from datetime import datetime, timedelta


def test_store_and_retrieve_message():
    """Test storing and retrieving messages."""
    service = ConversationMemoryService()
    call_sid = "test_call_123"
    
    service.store_message(call_sid, "user", "Hello")
    service.store_message(call_sid, "assistant", "Hi there!")
    
    history = service.get_history(call_sid)
    
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi there!"


def test_format_for_openai():
    """Test formatting conversation for OpenAI."""
    service = ConversationMemoryService()
    call_sid = "test_call_456"
    
    service.store_message(call_sid, "user", "What's my career path?")
    service.store_message(call_sid, "assistant", "Let's discuss your interests.")
    
    messages = service.format_for_openai(call_sid, system_prompt="You are a career advisor.")
    
    assert len(messages) == 3  # system + 2 messages
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are a career advisor."
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "assistant"


def test_clear_history():
    """Test clearing conversation history."""
    service = ConversationMemoryService()
    call_sid = "test_call_789"
    
    service.store_message(call_sid, "user", "Test message")
    assert len(service.get_history(call_sid)) == 1
    
    service.clear_history(call_sid)
    assert len(service.get_history(call_sid)) == 0


def test_conversation_stats():
    """Test getting conversation statistics."""
    service = ConversationMemoryService()
    call_sid = "test_call_stats"
    
    service.store_message(call_sid, "user", "Message 1")
    service.store_message(call_sid, "assistant", "Response 1")
    service.store_message(call_sid, "user", "Message 2")
    
    stats = service.get_conversation_stats(call_sid)
    
    assert stats is not None
    assert stats["message_count"] == 3
    assert stats["user_messages"] == 2
    assert stats["assistant_messages"] == 1
    assert stats["duration_minutes"] >= 0


def test_cleanup_old_conversations():
    """Test automatic cleanup of old conversations."""
    service = ConversationMemoryService(ttl_minutes=0)  # Immediate expiry for testing
    call_sid = "test_call_old"
    
    service.store_message(call_sid, "user", "Old message")
    
    # Manually set old timestamp
    service._conversations[call_sid]["last_updated"] = datetime.now() - timedelta(minutes=1)
    
    cleaned = service.cleanup_old_conversations()
    
    assert cleaned == 1
    assert len(service.get_history(call_sid)) == 0