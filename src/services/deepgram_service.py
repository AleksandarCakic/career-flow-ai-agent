"""Deepgram Speech-to-Text service."""
from deepgram import DeepgramClient
import logging
from src.config.settings import settings

logger = logging.getLogger(__name__)

class DeepgramService:
    """Service for Deepgram speech-to-text transcription."""
    
    def __init__(self):
        self.dg = DeepgramClient(api_key=settings.deepgram_api_key)

    def transcribe(self, audio_url: str, model: str = "nova-3", language: str = "en-US") -> str:
        """
        Transcribe audio from a URL using Deepgram.
        
        Args:
            audio_url: Public URL of the audio file
            model: Deepgram model to use
            language: Language code for transcription
            
        Returns:
            Transcribed text as a string
            
        Raises:
            ValueError: If transcription fails or transcript is empty
        """
        try:
            response = self.dg.listen.v1.media.transcribe_url(
                url=audio_url,
                model=model,
                language=language,
                smart_format=True,
                punctuate=True,
            )
            data = response.model_dump()
            transcript = (
                data.get("results", {})
                    .get("channels", [{}])[0]
                    .get("alternatives", [{}])[0]
                    .get("transcript", "")
            )
            if not transcript:
                logger.warning(f"Deepgram returned empty transcript for {audio_url}")
                raise ValueError("Transcript is empty")
            logger.info(f"Deepgram transcript successful for {audio_url}")
            return transcript
        except Exception as e:
            logger.error(f"Deepgram transcription failed for {audio_url}: {e}")
            raise