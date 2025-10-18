"""Service for ElevenLabs text-to-speech synthesis."""
import logging
import requests
from src.config.settings import settings

logger = logging.getLogger(__name__)

class ElevenLabsService:
    """Service for ElevenLabs TTS."""
    
    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        
    def synthesize(
        self,
        text: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default voice (Rachel)
        model_id: str = "eleven_monolingual_v1"
    ) -> bytes:
        """
        Synthesize text to speech using ElevenLabs.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            model_id: ElevenLabs model ID
            
        Returns:
            Audio data as bytes
            
        Raises:
            Exception: If synthesis fails
        """
        try:
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            data = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            logger.info(f"ElevenLabs synthesis successful for text length: {len(text)}")
            return response.content
            
        except Exception as e:
            logger.error(f"ElevenLabs synthesis failed: {e}")
            raise