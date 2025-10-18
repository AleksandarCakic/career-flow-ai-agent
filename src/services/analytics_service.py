"""Analytics service for tracking conversations and user interactions."""
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from typing import Optional, List, Dict, Any

from src.models import User, Conversation, Message, ConversationStatus, MessageRole


class AnalyticsService:
    """Service for analytics and conversation tracking."""
    
    def get_or_create_user(self, db: Session, phone_number: str) -> User:
        """Get existing user or create new one."""
        user = db.query(User).filter(User.phone_number == phone_number).first()
        
        if not user:
            user = User(
                id=uuid.uuid4(),
                phone_number=phone_number,
                created_at=datetime.now(UTC)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user
    
    def create_conversation(
        self, 
        db: Session, 
        call_sid: str, 
        phone_number: str
    ) -> Conversation:
        """Create a new conversation."""
        # Get or create user
        user = self.get_or_create_user(db, phone_number)
        
        # Update user's last call time
        user.last_call_at = datetime.now(UTC)  # type: ignore
        
        # Create conversation
        conversation = Conversation(
            id=uuid.uuid4(),
            call_sid=call_sid,
            user_id=user.id,
            phone_number=phone_number,
            started_at=datetime.now(UTC),
            status=ConversationStatus.ACTIVE
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        return conversation
    
    def log_message(
        self,
        db: Session,
        conversation_id: uuid.UUID | str,
        role: MessageRole,
        content: str,
        extra_data: Optional[str] = None
    ) -> Message:
        """Log a message in a conversation."""
        # Convert string to UUID if needed
        if isinstance(conversation_id, str):
            conversation_id = uuid.UUID(conversation_id)
        
        message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=datetime.now(UTC),
            extra_data=extra_data
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        return message
    
    def get_conversation_by_id(
        self,
        db: Session,
        conversation_id: uuid.UUID
    ) -> Optional[Conversation]:
        """Get conversation by ID."""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    def get_conversation_by_call_sid(
        self, 
        db: Session, 
        call_sid: str
    ) -> Optional[Conversation]:
        """Get conversation by Twilio call SID."""
        return db.query(Conversation).filter(Conversation.call_sid == call_sid).first()
    
    def get_conversation_messages(
        self,
        db: Session,
        conversation_id: uuid.UUID
    ) -> List[Message]:
        """Get all messages for a conversation."""
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp).all()
    
    def end_conversation(
        self,
        db: Session,
        call_sid: str,
        status: ConversationStatus = ConversationStatus.COMPLETED
    ) -> Optional[Conversation]:
        """End a conversation and calculate duration."""
        conversation = self.get_conversation_by_call_sid(db, call_sid)
        
        if conversation:
            conversation.ended_at = datetime.now(UTC)  # type: ignore
            conversation.status = status  # type: ignore
            
            # Calculate duration
            if conversation.started_at is not None:
                # Ensure started_at is timezone-aware for calculation
                started_at = conversation.started_at
                if started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=UTC)
                
                duration = conversation.ended_at - started_at  # type: ignore
                conversation.duration_seconds = int(duration.total_seconds())  # type: ignore
            
            db.commit()
            db.refresh(conversation)
        
        return conversation
    
    def get_all_conversations(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Conversation]:
        """Get all conversations with pagination."""
        return db.query(Conversation).order_by(
            Conversation.started_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_all_users(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get all users with pagination."""
        return db.query(User).order_by(
            User.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_user_conversations(
        self, 
        db: Session, 
        user_id: uuid.UUID
    ) -> List[Conversation]:
        """Get all conversations for a specific user."""
        return db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.started_at.desc()).all()
    
    def get_conversations_by_phone(
        self, 
        db: Session, 
        phone_number: str
    ) -> List[Conversation]:
        """Get all conversations for a phone number."""
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if not user:
            return []
        return self.get_user_conversations(db, user.id)  # type: ignore
    
    def get_user_by_phone(self, db: Session, phone_number: str) -> Optional[User]:
        """Get user by phone number."""
        return db.query(User).filter(User.phone_number == phone_number).first()
    
    def get_stats(self, db: Session) -> Dict[str, Any]:
        """Get overall statistics."""
        total_conversations = db.query(func.count(Conversation.id)).scalar()
        total_users = db.query(func.count(User.id)).scalar()
        total_messages = db.query(func.count(Message.id)).scalar()
        
        active_conversations = db.query(func.count(Conversation.id)).filter(
            Conversation.status == ConversationStatus.ACTIVE
        ).scalar()
        
        completed_conversations = db.query(func.count(Conversation.id)).filter(
            Conversation.status == ConversationStatus.COMPLETED
        ).scalar()
        
        # Calculate average duration for completed conversations
        avg_duration = db.query(func.avg(Conversation.duration_seconds)).filter(
            Conversation.duration_seconds.isnot(None)
        ).scalar()
        
        avg_messages = 0
        if total_conversations > 0:
            avg_messages = total_messages / total_conversations
        
        return {
            "total_users": total_users,
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "completed_conversations": completed_conversations,
            "total_messages": total_messages,
            "average_messages_per_conversation": round(avg_messages, 2),
            "average_duration_seconds": round(avg_duration, 2) if avg_duration else 0
        }