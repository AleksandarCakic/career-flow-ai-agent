"""Admin routes for prompt management."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from src.database import get_db
from src.services.prompt_optimizer_service import PromptOptimizer  # Note: Updated filename
from src.services.voice_service import VoiceService

router = APIRouter(prefix="/admin", tags=["admin"])
optimizer = PromptOptimizer()
voice_service = VoiceService()


@router.post("/analyze-conversations")
async def analyze_conversations(
    hours: int = 24,
    min_conversations: int = 1,  # Lower default for testing
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Analyze recent conversations and generate improvement suggestions."""
    
    # Analyze conversations
    analysis = optimizer.analyze_recent_conversations(
        db, 
        hours=hours,
        min_conversations=min_conversations
    )
    
    if analysis["status"] != "analyzed":
        return analysis
    
    # Generate improvements
    improvements = optimizer.generate_prompt_improvements(
        analysis=analysis,
        current_prompt=voice_service.system_prompt
    )
    
    return {
        "analysis": analysis,
        "improvements": improvements
    }


@router.get("/current-prompt")
async def get_current_prompt() -> Dict[str, Any]:
    """Get the current system prompt."""
    return {
        "prompt": voice_service.system_prompt,
        "length": len(voice_service.system_prompt)
    }