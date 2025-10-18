"""Admin routes for prompt management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from src.database import get_db
from src.services.prompt_optimizer_service import PromptOptimizerService
from src.services.voice_service import VoiceService

router = APIRouter(prefix="/admin", tags=["admin"])
voice_service = VoiceService()


@router.post("/analyze-conversations")
async def analyze_conversations(
    hours: int = 168,  # Default: last 7 days
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Analyze recent conversations and generate improvement suggestions."""
    
    try:
        # Initialize service (create new instance per request)
        optimizer = PromptOptimizerService()
        
        # Analyze conversations (does both pattern detection AND AI recommendations)
        result = optimizer.analyze_conversations(
            db=db,
            hours_back=hours
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/current-prompt")
async def get_current_prompt() -> Dict[str, Any]:
    """Get the current system prompt."""
    return {
        "prompt": voice_service.system_prompt,
        "length": len(voice_service.system_prompt)
    }