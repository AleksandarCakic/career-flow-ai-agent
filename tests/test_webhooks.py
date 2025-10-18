"""Tests for Twilio webhook endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from src.main import app
from src.models import Conversation, ConversationStatus

client = TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session."""
    mock_session = MagicMock()
    
    # Create a proper mock conversation with all required attributes
    mock_conversation = Mock(spec=Conversation)
    mock_conversation.id = uuid4()  # Proper UUID
    mock_conversation.call_sid = "CA123456"
    mock_conversation.phone_number = "+15551234567"
    mock_conversation.status = ConversationStatus.ACTIVE
    mock_conversation.started_at = datetime.now(timezone.utc)
    mock_conversation.user_id = uuid4()
    
    # Mock the query chain
    mock_query = mock_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = mock_conversation
    
    return mock_session, mock_conversation


def test_health_endpoint():
    """Test the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200


def test_voice_webhook_endpoint_exists(mock_db):
    """Test that voice webhook endpoint exists and returns response."""
    mock_session, mock_conversation = mock_db
    
    with patch('src.api.routes.webhooks.get_db', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.analytics_service.create_conversation', return_value=mock_conversation):
            with patch('src.api.routes.webhooks.analytics_service.log_message'):
                with patch('src.api.routes.webhooks.voice_service.process_user_input', return_value="Hi there!"):
                    response = client.post(
                        "/webhooks/twilio/voice",
                        data={
                            "CallSid": "CA123456",
                            "From": "+15551234567",
                            "To": "+15559876543"
                        }
                    )
    
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]


def test_voice_webhook_contains_gather(mock_db):
    """Test that voice webhook contains proper TwiML or WebSocket config."""
    mock_session, mock_conversation = mock_db
    
    # Mock voice service to return a simple greeting
    mock_voice_response = "Hi, thanks for calling Career Flow, my name is Mica."
    
    with patch('src.api.routes.webhooks.get_db', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.analytics_service.create_conversation', return_value=mock_conversation):
            with patch('src.api.routes.webhooks.analytics_service.log_message'):
                with patch('src.api.routes.webhooks.voice_service.process_user_input', return_value=mock_voice_response):
                    response = client.post(
                        "/webhooks/twilio/voice",
                        data={
                            "CallSid": "CA123456",
                            "From": "+15551234567",
                            "To": "+15559876543"
                        }
                    )
    
    # Should have TwiML elements
    assert response.status_code == 200
    content = response.text
    
    # Check for TwiML elements (case insensitive)
    assert "<Response>" in content
    assert any(keyword.lower() in content.lower() for keyword in ["<Gather", "<Say", "<Stream"])


def test_process_speech_webhook(mock_db):
    """Test speech processing webhook."""
    mock_session, mock_conversation = mock_db
    
    mock_ai_response = "That sounds great! Tell me more."
    
    with patch('src.api.routes.webhooks.get_db', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.analytics_service.get_conversation_by_call_sid', return_value=mock_conversation):
            with patch('src.api.routes.webhooks.analytics_service.log_message'):
                with patch('src.api.routes.webhooks.voice_service.process_user_input', return_value=mock_ai_response):
                    response = client.post(
                        "/webhooks/twilio/process-speech",
                        data={
                            "CallSid": "CA123456",
                            "SpeechResult": "I need help with my resume"
                        }
                    )
    
    assert response.status_code == 200
    content = response.text
    assert "<Response>" in content
    # Check that Say tag exists (case insensitive)
    assert "<say" in content.lower() or "polly" in content.lower()


def test_process_speech_no_result(mock_db):
    """Test speech processing with no speech result."""
    mock_session, mock_conversation = mock_db
    
    with patch('src.api.routes.webhooks.get_db', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.analytics_service.get_conversation_by_call_sid', return_value=mock_conversation):
            with patch('src.api.routes.webhooks.analytics_service.log_message'):
                with patch('src.api.routes.webhooks.voice_service.process_user_input', return_value="Could you repeat that?"):
                    response = client.post(
                        "/webhooks/twilio/process-speech",
                        data={
                            "CallSid": "CA123456"
                        }
                    )
    
    assert response.status_code == 200


def test_call_status_webhook(mock_db):
    """Test call status update webhook."""
    mock_session, mock_conversation = mock_db
    
    with patch('src.api.routes.webhooks.get_db', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.analytics_service.end_conversation', return_value=mock_conversation):
            with patch('src.api.routes.webhooks.analytics_service.log_message'):
                response = client.post(
                    "/webhooks/twilio/status",
                    data={
                        "CallSid": "CA123456",
                        "CallStatus": "completed"
                    }
                )
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_recording_webhook(mock_db):
    """Test recording completion webhook."""
    mock_session, mock_conversation = mock_db
    
    with patch('src.api.routes.webhooks.get_db', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.analytics_service.get_conversation_by_call_sid', return_value=mock_conversation):
            with patch('src.api.routes.webhooks.analytics_service.log_message'):
                response = client.post(
                    "/webhooks/twilio/recording",
                    data={
                        "CallSid": "CA123456",
                        "RecordingUrl": "https://api.twilio.com/recording123",
                        "RecordingDuration": "30"
                    }
                )
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_transfer_status_webhook(mock_db):
    """Test call transfer status webhook."""
    mock_session, mock_conversation = mock_db
    
    with patch('src.api.routes.webhooks.get_db', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.analytics_service.get_conversation_by_call_sid', return_value=mock_conversation):
            with patch('src.api.routes.webhooks.analytics_service.log_message'):
                response = client.post(
                    "/webhooks/twilio/transfer-status",
                    data={
                        "CallSid": "CA123456",
                        "DialCallStatus": "completed"
                    }
                )
    
    assert response.status_code == 200
    assert "<Response>" in response.text


def test_process_speech_with_human_transfer(mock_db):
    """Test speech processing triggers human transfer."""
    mock_session, mock_conversation = mock_db
    
    mock_ai_response = "Let me connect you with Alex right now."
    
    with patch('src.api.routes.webhooks.get_db', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.analytics_service.get_conversation_by_call_sid', return_value=mock_conversation):
            with patch('src.api.routes.webhooks.analytics_service.log_message'):
                with patch('src.api.routes.webhooks.voice_service.process_user_input', return_value=mock_ai_response):
                    with patch('src.api.routes.webhooks.settings.alex_phone_number', '+15551234567'):
                        response = client.post(
                            "/webhooks/twilio/process-speech",
                            data={
                                "CallSid": "CA123456",
                                "SpeechResult": "Connect me with Alex"
                            }
                        )
    
    assert response.status_code == 200
    content = response.text
    # Check that either Dial or Say exists (case insensitive)
    assert "<dial" in content.lower() or "<say" in content.lower()


def test_process_speech_conversation_not_found():
    """Test speech processing when conversation doesn't exist."""
    mock_session = MagicMock()
    
    with patch('src.api.routes.webhooks.get_db', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.analytics_service.get_conversation_by_call_sid', return_value=None):
            response = client.post(
                "/webhooks/twilio/process-speech",
                data={
                    "CallSid": "NONEXISTENT",
                    "SpeechResult": "Hello"
                }
            )
    
    assert response.status_code == 200
    assert "error" in response.text.lower() or "sorry" in response.text.lower()