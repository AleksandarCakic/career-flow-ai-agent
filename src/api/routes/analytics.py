"""Analytics and conversation history endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, UUID4
from datetime import datetime

from src.database import get_db_session
from src.services.analytics_service import AnalyticsService
from src.models.conversation import Conversation, Message

router = APIRouter()


# Pydantic schemas for responses
class MessageResponse(BaseModel):
    """Message response schema."""
    id: UUID4
    role: str
    content: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation response schema."""
    id: UUID4
    call_sid: str
    phone_number: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    status: str
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    """Detailed conversation with messages."""
    id: UUID4
    call_sid: str
    phone_number: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    status: str
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    """Analytics statistics response."""
    total_conversations: int
    total_messages: int
    average_duration_seconds: float
    active_conversations: int


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_session)
):
    """Get all conversations with pagination."""
    analytics = AnalyticsService()
    conversations = analytics.get_all_conversations(db, limit=limit, offset=offset)
    
    # Convert to response models
    result = []
    for conv in conversations:
        result.append(ConversationResponse(
            id=conv.id,  # type: ignore
            call_sid=conv.call_sid,  # type: ignore
            phone_number=conv.phone_number,  # type: ignore
            started_at=conv.started_at,  # type: ignore
            ended_at=conv.ended_at,  # type: ignore
            duration_seconds=conv.duration_seconds,  # type: ignore
            status=conv.status.value,  # type: ignore
            message_count=len(conv.messages) if conv.messages else 0
        ))
    
    return result


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID4,
    db: Session = Depends(get_db_session)
):
    """Get a specific conversation with all messages."""
    analytics = AnalyticsService()
    conversation = analytics.get_conversation_with_messages(db, str(conversation_id))
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Convert messages
    messages = [
        MessageResponse(
            id=msg.id,  # type: ignore
            role=msg.role.value,  # type: ignore
            content=msg.content,  # type: ignore
            timestamp=msg.timestamp  # type: ignore
        )
        for msg in conversation.messages
    ]
    
    return ConversationDetailResponse(
        id=conversation.id,  # type: ignore
        call_sid=conversation.call_sid,  # type: ignore
        phone_number=conversation.phone_number,  # type: ignore
        started_at=conversation.started_at,  # type: ignore
        ended_at=conversation.ended_at,  # type: ignore
        duration_seconds=conversation.duration_seconds,  # type: ignore
        status=conversation.status.value,  # type: ignore
        messages=messages
    )


@router.get("/conversations/call/{call_sid}", response_model=ConversationDetailResponse)
async def get_conversation_by_call_sid(
    call_sid: str,
    db: Session = Depends(get_db_session)
):
    """Get conversation by Twilio call SID."""
    analytics = AnalyticsService()
    conversation = analytics.get_conversation_by_call_sid(db, call_sid)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Convert messages
    messages = [
        MessageResponse(
            id=msg.id,  # type: ignore
            role=msg.role.value,  # type: ignore
            content=msg.content,  # type: ignore
            timestamp=msg.timestamp  # type: ignore
        )
        for msg in conversation.messages
    ]
    
    return ConversationDetailResponse(
        id=conversation.id,  # type: ignore
        call_sid=conversation.call_sid,  # type: ignore
        phone_number=conversation.phone_number,  # type: ignore
        started_at=conversation.started_at,  # type: ignore
        ended_at=conversation.ended_at,  # type: ignore
        duration_seconds=conversation.duration_seconds,  # type: ignore
        status=conversation.status.value,  # type: ignore
        messages=messages
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: Session = Depends(get_db_session)
):
    """Get overall conversation statistics."""
    analytics = AnalyticsService()
    stats = analytics.get_stats(db)
    
    return StatsResponse(**stats)


@router.get("/phone/{phone_number}/conversations", response_model=List[ConversationResponse])
async def get_conversations_by_phone(
    phone_number: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db_session)
):
    """Get all conversations for a specific phone number."""
    from sqlalchemy import desc
    
    conversations = db.query(Conversation).filter(
        Conversation.phone_number == phone_number
    ).order_by(desc(Conversation.started_at)).limit(limit).all()
    
    result = []
    for conv in conversations:
        result.append(ConversationResponse(
            id=conv.id,  # type: ignore
            call_sid=conv.call_sid,  # type: ignore
            phone_number=conv.phone_number,  # type: ignore
            started_at=conv.started_at,  # type: ignore
            ended_at=conv.ended_at,  # type: ignore
            duration_seconds=conv.duration_seconds,  # type: ignore
            status=conv.status.value,  # type: ignore
            message_count=len(conv.messages) if conv.messages else 0
        ))
    
    return result