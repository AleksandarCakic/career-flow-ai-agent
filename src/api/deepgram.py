from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from src.services.deepgram_service import DeepgramService

router = APIRouter()
deepgram_service = DeepgramService()

class TranscribeRequest(BaseModel):
    audio_url: HttpUrl

class TranscribeResponse(BaseModel):
    transcript: str

@router.post("/transcribe", response_model=TranscribeResponse)
def transcribe_audio(request: TranscribeRequest):
    try:
        transcript = deepgram_service.transcribe(str(request.audio_url))
        if not transcript:
            raise HTTPException(status_code=400, detail="Transcription failed or returned empty result.")
        return TranscribeResponse(transcript=transcript)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")