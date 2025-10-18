"""Voice service for handling AI conversation logic."""
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from openai import OpenAI

from src.config import settings
from src.services.analytics_service import AnalyticsService
from src.models import MessageRole

logger = logging.getLogger(__name__)


class VoiceService:
    """Service for processing voice conversations with AI."""
    
    def __init__(self):
        """Initialize voice service with OpenAI client."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.analytics_service = AnalyticsService()
        self.system_prompt = """You are a helpful career advisor assistant. 
You help people with:
- Resume writing and review
- Interview preparation
- Career guidance and planning
- Job search strategies
- Professional development

Keep your responses concise and conversational since this is a voice conversation.
Limit responses to 2-3 sentences.
Ask follow-up questions to better understand the user's needs.
Be encouraging and supportive."""
    
    async def process_user_input(
        self, 
        user_input: str,
        conversation_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> str:
        """
        Process user input and generate AI response.
        
        Args:
            user_input: The user's speech input
            conversation_id: Optional conversation ID to load history
            db: Optional database session for loading history
            
        Returns:
            AI generated response
        """
        try:
            # Build conversation history from database if available
            messages = [{"role": "system", "content": self.system_prompt}]
            
            if conversation_id and db:
                from uuid import UUID
                conversation_uuid = UUID(conversation_id)
                db_messages = self.analytics_service.get_conversation_messages(db, conversation_uuid)
                for msg in db_messages:
                    if str(msg.role) in [MessageRole.USER.value, MessageRole.ASSISTANT.value]:
                        role = "user" if str(msg.role) == MessageRole.USER.value else "assistant"
                        messages.append({
                            "role": role,
                            "content": str(msg.content)
                        })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Convert message dicts to OpenAI ChatCompletionMessageParam objects
            from openai.types.chat import (
                ChatCompletionSystemMessageParam,
                ChatCompletionUserMessageParam,
                ChatCompletionAssistantMessageParam
            )
            def to_message_param(msg):
                if msg["role"] == "system":
                    return ChatCompletionSystemMessageParam(role="system", content=msg["content"])
                elif msg["role"] == "user":
                    return ChatCompletionUserMessageParam(role="user", content=msg["content"])
                elif msg["role"] == "assistant":
                    return ChatCompletionAssistantMessageParam(role="assistant", content=msg["content"])
                else:
                    raise ValueError(f"Unknown role: {msg['role']}")
            message_params = [to_message_param(m) for m in messages[-11:]]

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # or "gpt-4" for better quality
                messages=message_params,  # System + last 10 messages
                max_tokens=150,  # Keep responses short for voice
                temperature=0.7
            )
            
            # Extract assistant response
            assistant_message = response.choices[0].message.content or ""
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return "I'm sorry, I encountered an error. Could you please repeat that?"