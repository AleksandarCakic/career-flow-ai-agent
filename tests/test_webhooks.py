"""Tests for Twilio webhook handlers."""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_voice_webhook_endpoint_exists():
    """Test that voice webhook endpoint exists."""
    response = client.post("/webhook/twilio/voice")
    # Should return 200 and XML (TwiML)
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<Response>" in response.text
    assert "Mica" in response.text


def test_voice_webhook_contains_gather():
    """Test that voice webhook includes speech gathering."""
    response = client.post("/webhook/twilio/voice")
    assert response.status_code == 200
    assert "<Gather" in response.text
    assert 'input="speech"' in response.text


def test_process_speech_endpoint():
    """Test speech processing endpoint."""
    response = client.post(
        "/webhook/twilio/process-speech",
        data={
            "SpeechResult": "I love solving complex problems",
            "CallSid": "test_call_123"
        }
    )
    assert response.status_code == 200
    assert "<Response>" in response.text
    assert "Thank you" in response.text


def test_process_speech_no_result():
    """Test speech processing with no result."""
    response = client.post(
        "/webhook/twilio/process-speech",
        data={
            "SpeechResult": "",
            "CallSid": "test_call_123"
        }
    )
    assert response.status_code == 200
    assert "didn't catch that" in response.text