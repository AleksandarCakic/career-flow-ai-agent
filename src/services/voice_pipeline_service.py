"""Service to orchestrate the full voice AI pipeline."""
import logging
from src.services.deepgram_service import DeepgramService
from src.services.ai_service import AIService
from src.services.elevenlabs_service import ElevenLabsService

logger = logging.getLogger(__name__)

class VoicePipelineService:
    """Orchestrates STT → AI → TTS pipeline."""
    
    def __init__(self):
        self.deepgram = DeepgramService()
        self.ai = AIService()
        self.elevenlabs = ElevenLabsService()
        
    def process_audio_to_audio(
        self,
        audio_url: str,
        system_prompt: str = "You are a helpful career advisor assistant."
    ) -> bytes:
        """
        Process audio input through full pipeline and return audio response.
        """
        try:
            # Step 1: Transcribe audio to text
            logger.info(f"Step 1: Transcribing audio from {audio_url}")
            transcript = self.deepgram.transcribe(audio_url)
            if not transcript:
                raise ValueError("Transcription returned empty result")
            logger.info(f"Transcript: {transcript}")
            
            # Step 2: Generate AI response
            logger.info("Step 2: Generating AI response")
            try:
                ai_response = self.ai.generate_response(transcript, system_prompt)
                logger.info(f"AI Response: {ai_response}")
            except Exception as e:
                logger.error(f"AI service failed: {e}")
                raise Exception(f"Anthropic API error: {e}")
            
            # Step 3: Synthesize response to audio
            logger.info("Step 3: Synthesizing audio response")
            try:
                audio_response = self.elevenlabs.synthesize(ai_response)
                logger.info("Pipeline completed successfully")
                return audio_response
            except Exception as e:
                logger.error(f"ElevenLabs service failed: {e}")
                raise Exception(f"ElevenLabs API error: {e}")
            
        except Exception as e:
            logger.error(f"Voice pipeline failed: {e}")
            raise