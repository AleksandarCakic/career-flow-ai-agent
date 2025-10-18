"""API endpoints for voice AI pipeline."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, HttpUrl, ConfigDict
from src.services.voice_pipeline_service import VoicePipelineService

router = APIRouter()
pipeline_service = VoicePipelineService()

class VoicePipelineRequest(BaseModel):
    """Request model for voice pipeline endpoint."""
    audio_url: HttpUrl
    system_prompt: str = "You are a helpful career advisor assistant."
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "audio_url": "https://dpgr.am/bueller.wav",
                "system_prompt": "You are a helpful career advisor assistant."
            }
        }
    )

@router.post(
    "/process",
    summary="Process audio through full voice AI pipeline",
    response_class=Response
)
def process_voice_pipeline(request: VoicePipelineRequest):
    """
    Process audio through STT → AI → TTS pipeline and return audio response.
    
    Returns audio/mpeg content.
    """
    try:
        audio_response = pipeline_service.process_audio_to_audio(
            str(request.audio_url),
            request.system_prompt
        )
        return Response(
            content=audio_response,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=response.mp3"
            }
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")