"""Tests for Deepgram STT service."""
from src.services.deepgram_service import DeepgramService
from src.config.settings import settings

def test_deepgram_transcribe(monkeypatch):
    """Test Deepgram transcription with a mock response."""
    # Patch the DeepgramService to use a dummy API key from settings
    monkeypatch.setattr(settings, "deepgram_api_key", "test_key")
    service = DeepgramService()

    def mock_transcribe_url(*args, **kwargs):
        class MockResponse:
            def model_dump(self):
                return {
                    "results": {
                        "channels": [
                            {
                                "alternatives": [
                                    {"transcript": "This is a test transcript."}
                                ]
                            }
                        ]
                    }
                }
        return MockResponse()

    # Patch the transcribe_url method on the DeepgramClient's listen.v1.media
    monkeypatch.setattr(
        type(service.dg.listen.v1.media),
        "transcribe_url",
        lambda *args, **kwargs: mock_transcribe_url()
    )

    transcript = service.transcribe("http://fake-url.com/audio.wav")
    assert transcript == "This is a test transcript."