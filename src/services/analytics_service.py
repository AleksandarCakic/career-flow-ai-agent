"""Service for logging and analyzing conversations."""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from src.models.conversation import Conversation, Message, ConversationStatus, MessageRole
from src.database import get_db

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for conversation analytics and logging."""
    
    @staticmethod
    def create_conversation(
        db: Session,
        call_sid: str,
        phone_number: str
    ) -> Conversation:
        """
        Create a new conversation record.
        
        Args:
            db: Database session
            call_sid: Twilio call SID
            phone_number: Caller's phone number
            
        Returns:
            Created Conversation object
        """
        conversation = Conversation(
            call_sid=call_sid,
            phone_number=phone_number,
            started_at=datetime.utcnow(),
            status=ConversationStatus.ACTIVE
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        logger.info(f"Created conversation {conversation.id} for call {call_sid}")
        return conversation
    
    @staticmethod
    def log_message(
        db: Session,
        conversation_id: str,
        role: MessageRole,
        content: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Log a message in a conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation UUID
            role: Message role (user/assistant/system)
            content: Message content
            extra_data: Optional metadata
            
        Returns:
            Created Message object
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            extra_data=extra_data
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        
        logger.debug(f"Logged {role} message for conversation {conversation_id}")
        return message
    
    @staticmethod
    def end_conversation(
        db: Session,
        call_sid: str,
        status: ConversationStatus = ConversationStatus.COMPLETED
    ) -> Optional[Conversation]:
        """
        Mark a conversation as ended.
        
        Args:
            db: Database session
            call_sid: Twilio call SID
            status: Final conversation status
            
        Returns:
            Updated Conversation object or None if not found
        """
        conversation = db.query(Conversation).filter(
            Conversation.call_sid == call_sid
        ).first()
        
        if not conversation:
            logger.warning(f"Conversation not found for call {call_sid}")
            return None
        
        # Assign to the instance attribute, not the Column object
        setattr(conversation, 'ended_at', datetime.utcnow())
        setattr(conversation, 'status', status.value if hasattr(status, "value") else str(status))
        
        if getattr(conversation, "started_at", None) is not None:
            duration = (conversation.ended_at - conversation.started_at).total_seconds()
            setattr(conversation, 'duration_seconds', int(duration))
        
        db.commit()
        db.refresh(conversation)
        
        logger.info(f"Ended conversation {conversation.id} with status {status}")
        return conversation
    
    @staticmethod
    def get_conversation_by_call_sid(
        db: Session,
        call_sid: str
    ) -> Optional[Conversation]:
        """Get conversation by Twilio call SID."""
        return db.query(Conversation).filter(
            Conversation.call_sid == call_sid
        ).first()
    
    @staticmethod
    def get_all_conversations(
        db: Session,
        limit: int = 100,
        offset: int = 0
    ) -> List[Conversation]:
        """Get all conversations with pagination."""
        return db.query(Conversation).order_by(
            desc(Conversation.started_at)
        ).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_conversation_with_messages(
        db: Session,
        conversation_id: str
    ) -> Optional[Conversation]:
        """Get conversation with all messages."""
        return db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
    
    @staticmethod
    def get_stats(db: Session) -> Dict[str, Any]:
        """
        Get overall conversation statistics.
        
        Returns:
            Dictionary with stats
        """
        total_conversations = db.query(func.count(Conversation.id)).scalar()
        total_messages = db.query(func.count(Message.id)).scalar()
        
        avg_duration = db.query(
            func.avg(Conversation.duration_seconds)
        ).filter(
            Conversation.duration_seconds.isnot(None)
        ).scalar()
        
        active_conversations = db.query(func.count(Conversation.id)).filter(
            Conversation.status == ConversationStatus.ACTIVE
        ).scalar()
        
        return {
            "total_conversations": total_conversations or 0,
            "total_messages": total_messages or 0,
            "average_duration_seconds": float(avg_duration) if avg_duration else 0,
            "active_conversations": active_conversations or 0
        }