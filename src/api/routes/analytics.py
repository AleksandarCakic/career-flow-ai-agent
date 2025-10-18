"""Analytics endpoints for viewing conversation data."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from src.database import get_db
from src.services.analytics_service import AnalyticsService
from src.models import Conversation, User

router = APIRouter()
analytics_service = AnalyticsService()


@router.get("/conversations")
def get_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get all conversations with pagination."""
    try:
        conversations = analytics_service.get_all_conversations(db, skip=skip, limit=limit)
        return {
            "conversations": conversations,
            "count": len(conversations),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific conversation by ID."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")
    
    try:
        conversation = analytics_service.get_conversation_by_id(db, conv_uuid)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/conversations/call/{call_sid}")
def get_conversation_by_call_sid(
    call_sid: str,
    db: Session = Depends(get_db)
):
    """Get a specific conversation by call SID."""
    try:
        conversation = analytics_service.get_conversation_by_call_sid(db, call_sid)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get all messages for a specific conversation."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")
    
    try:
        messages = analytics_service.get_conversation_messages(db, conv_uuid)
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "count": len(messages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/users")
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get all users with pagination."""
    try:
        users = analytics_service.get_all_users(db, skip=skip, limit=limit)
        return {
            "users": users,
            "count": len(users),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/users/{phone_number}")
def get_user(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """Get user information by phone number."""
    # Validate phone number format
    if not phone_number.startswith("+"):
        raise HTTPException(status_code=400, detail="Phone number must start with +")
    
    try:
        user = analytics_service.get_user_by_phone(db, phone_number)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/users/{phone_number}/conversations")
def get_user_conversations(
    phone_number: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get all conversations for a specific phone number."""
    # Validate phone number format
    if not phone_number.startswith("+"):
        raise HTTPException(status_code=400, detail="Phone number must start with +")
    
    try:
        conversations = analytics_service.get_conversations_by_phone(db, phone_number)
        
        # Apply pagination
        paginated = conversations[skip:skip + limit]
        
        return {
            "phone_number": phone_number,
            "conversations": paginated,
            "total_count": len(conversations),
            "count": len(paginated),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get overall analytics statistics."""
    try:
        return analytics_service.get_stats(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")