import pytest
from fastapi.testclient import TestClient
from src.main import app

def test_transcribe_endpoint(monkeypatch, client):
    """Test Deepgram transcription endpoint with mocked service."""
    from src.services.deepgram_service import DeepgramService
    monkeypatch.setattr(DeepgramService, "transcribe", lambda self, url: "Test transcript")
    
    response = client.post("/deepgram/transcribe", json={"audio_url": "https://dpgr.am/bueller.wav"})
    assert response.status_code == 200
    assert response.json() == {"transcript": "Test transcript"}

def test_transcribe_endpoint_invalid_url(client):
    """Test endpoint with invalid URL returns 422."""
    response = client.post("/deepgram/transcribe", json={"audio_url": "not-a-url"})
    assert response.status_code == 422

def test_transcribe_endpoint_empty_transcript(monkeypatch, client):
    """Test endpoint when transcription returns empty string."""
    from src.services.deepgram_service import DeepgramService
    monkeypatch.setattr(DeepgramService, "transcribe", lambda self, url: "")
    
    response = client.post("/deepgram/transcribe", json={"audio_url": "https://dpgr.am/bueller.wav"})
    assert response.status_code == 400
    assert "Transcription failed" in response.json()["detail"]