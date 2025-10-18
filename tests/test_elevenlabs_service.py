import pytest
from unittest.mock import Mock, patch

def test_elevenlabs_service_synthesize(monkeypatch):
    """Test ElevenLabs TTS synthesis."""
    from src.services.elevenlabs_service import ElevenLabsService
    
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.content = b"fake_audio_data"
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        service = ElevenLabsService()
        result = service.synthesize("Test text")
        
        assert result == b"fake_audio_data"
        mock_post.assert_called_once()