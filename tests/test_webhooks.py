"""Tests for Twilio webhook endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from src.main import app
from src.models.conversation import Conversation, ConversationStatus
import uuid

client = TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session."""
    mock_session = MagicMock()
    
    # Mock conversation object
    mock_conversation = Mock(spec=Conversation)
    mock_conversation.id = uuid.uuid4()
    mock_conversation.call_sid = "CA123456"
    mock_conversation.phone_number = "+15551234567"
    mock_conversation.status = ConversationStatus.ACTIVE
    
    # Mock query chain
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_conversation
    mock_session.query.return_value = mock_query
    
    return mock_session, mock_conversation


def test_voice_webhook_endpoint_exists(mock_db):
    """Test that voice webhook endpoint exists and returns TwiML."""
    mock_session, mock_conversation = mock_db
    
    with patch('src.api.routes.webhooks.get_db_session', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.AnalyticsService.create_conversation', return_value=mock_conversation):
            with patch('src.api.routes.webhooks.AnalyticsService.log_message'):
                response = client.post(
                    "/webhooks/twilio/voice",
                    data={"CallSid": "CA123456", "From": "+15551234567"}
                )
    
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<Response>" in response.text


def test_voice_webhook_contains_gather(mock_db):
    """Test that voice webhook contains Gather element for speech input."""
    mock_session, mock_conversation = mock_db
    
    with patch('src.api.routes.webhooks.get_db_session', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.AnalyticsService.create_conversation', return_value=mock_conversation):
            with patch('src.api.routes.webhooks.AnalyticsService.log_message'):
                response = client.post(
                    "/webhooks/twilio/voice",
                    data={"CallSid": "CA123456", "From": "+15551234567"}
                )
    
    assert "<Gather" in response.text
    assert 'input="speech"' in response.text
    assert "career advisor" in response.text.lower()


def test_process_speech_endpoint(mock_db):
    """Test process-speech endpoint with sample input."""
    mock_session, mock_conversation = mock_db
    
    with patch('src.api.routes.webhooks.get_db_session', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.AnalyticsService.get_conversation_by_call_sid', return_value=mock_conversation):
            with patch('src.api.routes.webhooks.AnalyticsService.log_message'):
                with patch('src.services.ai_service.AIService.generate_response', return_value="Thank you for sharing that!"):
                    response = client.post(
                        "/webhooks/twilio/process-speech",
                        data={
                            "SpeechResult": "I need help with my resume",
                            "CallSid": "CA123456"
                        }
                    )
    
    assert response.status_code == 200
    assert "Thank you for sharing that!" in response.text


def test_process_speech_no_result(mock_db):
    """Test process-speech endpoint with no speech input."""
    mock_session, mock_conversation = mock_db
    
    with patch('src.api.routes.webhooks.get_db_session', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.AnalyticsService.get_conversation_by_call_sid', return_value=mock_conversation):
            response = client.post(
                "/webhooks/twilio/process-speech",
                data={
                    "SpeechResult": "",
                    "CallSid": "CA123456"
                }
            )
    
    assert response.status_code == 200
    assert "I didn't catch that" in response.text


def test_process_speech_goodbye(mock_db):
    """Test that goodbye keywords end the call."""
    mock_session, mock_conversation = mock_db
    
    with patch('src.api.routes.webhooks.get_db_session', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.AnalyticsService.get_conversation_by_call_sid', return_value=mock_conversation):
            with patch('src.api.routes.webhooks.AnalyticsService.log_message'):
                with patch('src.api.routes.webhooks.AnalyticsService.end_conversation'):
                    response = client.post(
                        "/webhooks/twilio/process-speech",
                        data={
                            "SpeechResult": "goodbye",
                            "CallSid": "CA123456"
                        }
                    )
    
    assert response.status_code == 200
    assert "<Hangup" in response.text
    assert "Thank you" in response.text


def test_call_status_webhook(mock_db):
    """Test call status webhook."""
    mock_session, mock_conversation = mock_db
    
    with patch('src.api.routes.webhooks.get_db_session', return_value=iter([mock_session])):
        with patch('src.api.routes.webhooks.AnalyticsService.end_conversation'):
            response = client.post(
                "/webhooks/twilio/call-status",
                data={
                    "CallSid": "CA123456",
                    "CallStatus": "completed"
                }
            )
    
    assert response.status_code == 200
    assert response.text == "OK"