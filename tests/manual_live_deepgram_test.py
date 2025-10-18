"""
Manual test for Deepgram integration.
Run this script to perform a live transcription using Deepgram. Transcript will be printed to console.
Not a unit test—does not run with pytest.
"""
from src.services.deepgram_service import DeepgramService

if __name__ == "__main__":
    service = DeepgramService()
    audio_url = "https://dpgr.am/bueller.wav"
    transcript = service.transcribe(audio_url)
    print("Transcript:", transcript)