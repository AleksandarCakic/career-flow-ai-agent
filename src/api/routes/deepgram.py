from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, ConfigDict
from src.services.deepgram_service import DeepgramService

router = APIRouter()
deepgram_service = DeepgramService()

class TranscribeRequest(BaseModel):
    """Request model for Deepgram transcription endpoint."""
    audio_url: HttpUrl
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "audio_url": "https://dpgr.am/bueller.wav"
            }
        }
    )

class TranscribeResponse(BaseModel):
    """Response model for Deepgram transcription endpoint."""
    transcript: str

@router.post(
    "/transcribe",
    response_model=TranscribeResponse,
    summary="Transcribe audio from a public URL using Deepgram"
)
def transcribe_audio(request: TranscribeRequest):
    """
    Transcribe audio from a public URL using Deepgram and return the transcript.
    """
    try:
        transcript = deepgram_service.transcribe(str(request.audio_url))
        if not transcript:
            raise HTTPException(status_code=400, detail="Transcription failed or returned empty result.")
        return TranscribeResponse(transcript=transcript)
    except HTTPException:
        raise  # Re-raise HTTPException as-is
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")