import pytest
from unittest.mock import Mock, patch

def test_voice_pipeline_process_audio_to_audio(monkeypatch):
    """Test full voice pipeline."""
    from src.services.voice_pipeline_service import VoicePipelineService
    
    # Mock all services
    monkeypatch.setattr("src.services.deepgram_service.DeepgramService.transcribe", 
                       lambda self, url: "Test transcript")
    monkeypatch.setattr("src.services.ai_service.AIService.generate_response",
                       lambda self, msg, prompt: "AI response")
    monkeypatch.setattr("src.services.elevenlabs_service.ElevenLabsService.synthesize",
                       lambda self, text: b"audio_data")
    
    service = VoicePipelineService()
    result = service.process_audio_to_audio("https://example.com/audio.mp3")
    
    assert result == b"audio_data"