"""Tests for Twilio webhook endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock
from src.main import app
from src.models import Conversation, ConversationStatus
import uuid

client = TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session and conversation."""
    mock_session = MagicMock()
    
    # Mock conversation
    mock_conversation = Mock(spec=Conversation)
    mock_conversation.id = uuid.uuid4()
    mock_conversation.call_sid = "CA123456"
    mock_conversation.phone_number = "+15551234567"
    mock_conversation.status = ConversationStatus.ACTIVE
    
    # Setup query chain
    mock_session.query.return_value.filter.return_value.first.return_value = mock_conversation
    
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
            response = client.post(
                "/webhooks/twilio/voice",
                data={
                    "CallSid": "CA123456",
                    "From": "+15551234567",
                    "To": "+15559876543"  # Added missing parameter
                }
            )
    
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]


def test_voice_webhook_contains_gather(mock_db):
    """Test that voice webhook contains proper TwiML or WebSocket config."""
    mock_session, mock_conversation = mock_db
    
    with patch('src.api.routes.webhooks.get_db', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.analytics_service.create_conversation', return_value=mock_conversation):
            response = client.post(
                "/webhooks/twilio/voice",
                data={
                    "CallSid": "CA123456",
                    "From": "+15551234567",
                    "To": "+15559876543"  # Added missing parameter
                }
            )
    
    # Should have either WebSocket stream or Gather element
    assert response.status_code == 200
    content = response.text
    
    # Check for TwiML elements
    assert "<Response>" in content
    assert any(keyword in content for keyword in ["<Gather>", "<Say>", "<Stream>"])


def test_call_status_webhook(mock_db):
    """Test call status webhook."""
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