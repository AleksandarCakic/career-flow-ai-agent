"""Service for managing conversation history and context."""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConversationMemoryService:
    """Manages conversation history for active calls."""
    
    def __init__(self, ttl_minutes: int = 60):
        """
        Initialize conversation memory service.
        
        Args:
            ttl_minutes: Time-to-live for conversation history (default: 60 minutes)
        """
        self._conversations: Dict[str, Dict] = {}
        self.ttl_minutes = ttl_minutes
    
    def store_message(self, call_sid: str, role: str, content: str) -> None:
        """
        Store a message in conversation history.
        
        Args:
            call_sid: Twilio call SID
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        if call_sid not in self._conversations:
            self._conversations[call_sid] = {
                "messages": [],
                "created_at": datetime.now(),
                "last_updated": datetime.now()
            }
        
        self._conversations[call_sid]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        })
        self._conversations[call_sid]["last_updated"] = datetime.now()
        
        logger.info(f"Stored {role} message for call {call_sid}: {content[:50]}...")
    
    def get_history(self, call_sid: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a call.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            List of messages in format [{"role": "user", "content": "..."}]
        """
        if call_sid not in self._conversations:
            return []
        
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self._conversations[call_sid]["messages"]
        ]
    
    def format_for_openai(
        self, 
        call_sid: str, 
        system_prompt: str = "You are a helpful career advisor assistant."
    ) -> List[Dict[str, str]]:
        """
        Format conversation history for OpenAI API.
        
        Args:
            call_sid: Twilio call SID
            system_prompt: System message to prepend
            
        Returns:
            Messages array for OpenAI API with system prompt + history
        """
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.get_history(call_sid))
        return messages
    
    def clear_history(self, call_sid: str) -> None:
        """
        Clear conversation history for a call.
        
        Args:
            call_sid: Twilio call SID
        """
        if call_sid in self._conversations:
            del self._conversations[call_sid]
            logger.info(f"Cleared history for call {call_sid}")
    
    def cleanup_old_conversations(self) -> int:
        """
        Remove conversations older than TTL.
        
        Returns:
            Number of conversations cleaned up
        """
        cutoff_time = datetime.now() - timedelta(minutes=self.ttl_minutes)
        old_sids = [
            sid for sid, conv in self._conversations.items()
            if conv["last_updated"] < cutoff_time
        ]
        
        for sid in old_sids:
            del self._conversations[sid]
        
        if old_sids:
            logger.info(f"Cleaned up {len(old_sids)} old conversations")
        
        return len(old_sids)
    
    def get_conversation_stats(self, call_sid: str) -> Optional[Dict]:
        """
        Get statistics for a conversation.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            Dict with conversation stats or None if not found
        """
        if call_sid not in self._conversations:
            return None
        
        conv = self._conversations[call_sid]
        messages = conv["messages"]
        
        return {
            "message_count": len(messages),
            "user_messages": sum(1 for m in messages if m["role"] == "user"),
            "assistant_messages": sum(1 for m in messages if m["role"] == "assistant"),
            "duration_minutes": (datetime.now() - conv["created_at"]).total_seconds() / 60,
            "created_at": conv["created_at"],
            "last_updated": conv["last_updated"]
        }


# Global singleton instance
_memory_service = ConversationMemoryService()


def get_memory_service() -> ConversationMemoryService:
    """Get the global conversation memory service instance."""
    return _memory_service