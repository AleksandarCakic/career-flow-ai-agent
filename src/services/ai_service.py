"""Service for AI response generation using OpenAI."""
import logging
from typing import List, Dict, Optional
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)
from src.config.settings import settings

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered response generation."""
    
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is not configured")
        self.client = OpenAI(api_key=settings.openai_api_key)
        
    def generate_response(
        self,
        user_message: str,
        system_prompt: str = "You are a helpful career advisor assistant.",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        model: str = "gpt-4o",
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """
        Generate AI response to user message.
        
        Args:
            user_message: User's input text
            system_prompt: System instructions for the AI
            conversation_history: Previous messages in format [{"role": "...", "content": "..."}]
            model: OpenAI model to use (gpt-4o, gpt-4o-mini, gpt-3.5-turbo)
            max_tokens: Maximum tokens in response
            temperature: Randomness (0-2, lower = more focused)
            
        Returns:
            AI-generated response text
            
        Raises:
            Exception: If generation fails
        """
        try:
            # Build messages array with proper types
            messages: List[ChatCompletionMessageParam] = []
            
            if conversation_history:
                # Convert history to proper message types
                for msg in conversation_history:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    
                    if role == "system":
                        messages.append(ChatCompletionSystemMessageParam(role="system", content=content))
                    elif role == "user":
                        messages.append(ChatCompletionUserMessageParam(role="user", content=content))
                    elif role == "assistant":
                        messages.append(ChatCompletionAssistantMessageParam(role="assistant", content=content))
                
                # Add new user message
                messages.append(ChatCompletionUserMessageParam(role="user", content=user_message))
            else:
                # No history, create new conversation
                messages = [
                    ChatCompletionSystemMessageParam(role="system", content=system_prompt),
                    ChatCompletionUserMessageParam(role="user", content=user_message)
                ]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            response_text = response.choices[0].message.content or ""
            logger.info(f"AI response generated for message length: {len(user_message)}")
            return response_text
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            raise