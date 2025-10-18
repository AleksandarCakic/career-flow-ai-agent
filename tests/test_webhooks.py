"""Tests for Twilio webhooks."""
import pytest
from fastapi.testclient import TestClient
from src.main import app
from unittest.mock import Mock, patch

client = TestClient(app)


def test_voice_webhook_endpoint_exists():
    """Test that voice webhook endpoint exists."""
    response = client.post("/webhooks/twilio/voice")
    # Should return 200 and XML (TwiML)
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<Response>" in response.text
    assert "<Gather" in response.text  # Changed from checking for "Mica"


def test_voice_webhook_contains_gather():
    """Test that voice webhook includes speech gathering."""
    response = client.post("/webhooks/twilio/voice")
    assert response.status_code == 200
    content = response.text
    # Check for TwiML Gather element
    assert "<Gather" in content
    assert 'input="speech"' in content
    assert "<Say>" in content


def test_process_speech_endpoint():
    """Test speech processing endpoint with mocked AI."""
    # Mock the AI service to avoid real API calls
    with patch('src.api.routes.webhooks.AIService') as mock_ai_class:
        mock_ai_instance = Mock()
        mock_ai_instance.generate_response.return_value = "Thank you for sharing that!"
        mock_ai_class.return_value = mock_ai_instance
        
        response = client.post(
            "/webhooks/twilio/process-speech",
            data={
                "SpeechResult": "I love solving complex problems",
                "CallSid": "test_call_123"
            }
        )
        assert response.status_code == 200
        assert "<Response>" in response.text
        assert "Thank you for sharing that!" in response.text


def test_process_speech_no_result():
    """Test speech processing with no result."""
    response = client.post(
        "/webhooks/twilio/process-speech",
        data={
            "SpeechResult": "",
            "CallSid": "test_call_123"
        }
    )
    assert response.status_code == 200
    assert "I didn't catch that" in response.text