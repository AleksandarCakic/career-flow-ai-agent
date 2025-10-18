"""Automated prompt optimization based on conversation analysis."""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from openai import OpenAI

from src.config import settings
from src.models import Conversation, Message, MessageRole
from src.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


class PromptOptimizer:
    """Analyzes conversations and suggests prompt improvements."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.analytics_service = AnalyticsService()
    
    def analyze_recent_conversations(
        self, 
        db: Session, 
        hours: int = 24,
        min_conversations: int = 5
    ) -> Dict[str, Any]:
        """Analyze recent conversations for issues and patterns."""
        
        # Get conversations from last N hours
        since = datetime.utcnow() - timedelta(hours=hours)
        conversations = db.query(Conversation).filter(
            Conversation.started_at >= since
        ).all()
        
        if len(conversations) < min_conversations:
            logger.info(f"Not enough conversations ({len(conversations)}) for analysis")
            return {"status": "insufficient_data", "count": len(conversations)}
        
        issues = {
            "technical_errors": 0,
            "transfer_failures": 0,
            "multiple_questions": 0,
            "long_conversations": 0,
            "name_not_collected": 0
        }
        
        conversation_summaries = []
        
        for conv in conversations:
            import uuid
            messages = self.analytics_service.get_conversation_messages(db, uuid.UUID(str(conv.id)))
            
            user_msgs = [m for m in messages if getattr(m, "role", None) == MessageRole.USER]
            assistant_msgs = [m for m in messages if getattr(m, "role", None) == MessageRole.ASSISTANT]
            
            # Check for technical errors
            if any("technical hiccup" in m.content for m in assistant_msgs):
                issues["technical_errors"] += 1
            
            # Check for transfer attempts
            transfer_requested = any(
                keyword in m.content.lower() 
                for m in user_msgs 
                for keyword in ["connect", "transfer", "human", "speak to"]
            )
            if transfer_requested:
                transfer_handled = any(
                    "connect you" in m.content.lower() or "connecting" in m.content.lower()
                    for m in assistant_msgs
                )
                if not transfer_handled:
                    issues["transfer_failures"] += 1
            
            # Check for multiple questions
            if any(
                ("1." in m.content and "2." in m.content) or "Here are" in m.content
                for m in assistant_msgs
            ):
                issues["multiple_questions"] += 1
            
            # Check conversation length
            if len(user_msgs) > 10:
                issues["long_conversations"] += 1
            
            # Check name collection
            name_provided = any(
                any(word in m.content.lower() for word in ["my name", "i'm", "call me"])
                for m in user_msgs
            )
            if len(user_msgs) > 3 and not name_provided:
                issues["name_not_collected"] += 1
            
            # Create summary
            conversation_summaries.append({
                "call_sid": conv.call_sid,
                "exchanges": len(user_msgs),
                "duration": conv.duration_seconds,
                "sample_messages": [
                    {"role": m.role.value, "content": m.content[:100]}
                    for m in messages[:10]
                ]
            })
        
        return {
            "status": "analyzed",
            "period": f"last {hours} hours",
            "total_conversations": len(conversations),
            "issues": issues,
            "conversation_samples": conversation_summaries[:5]
        }
    
    def generate_prompt_improvements(
        self, 
        analysis: Dict[str, Any],
        current_prompt: str
    ) -> Dict[str, Any]:
        """Use AI to suggest prompt improvements based on analysis."""
        
        if analysis.get("status") != "analyzed":
            return {"status": "no_improvements", "reason": "insufficient_data"}
        
        analysis_prompt = f"""
You are an AI prompt engineer. Analyze these conversation issues and suggest improvements.

CURRENT ISSUES (from {analysis['total_conversations']} conversations):
{self._format_issues(analysis['issues'])}

TASK:
1. Identify the top 3 most critical issues
2. Suggest specific prompt modifications to address each issue
3. Provide improved sections (not entire prompt)

Format as JSON:
{{
    "critical_issues": ["issue1", "issue2", "issue3"],
    "improvements": [
        {{
            "issue": "issue name",
            "suggestion": "specific change to make",
            "reasoning": "why this helps"
        }}
    ],
    "confidence": "high/medium/low"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert AI prompt engineer."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            improvements = response.choices[0].message.content
            
            return {
                "status": "improvements_generated",
                "improvements": improvements,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate improvements: {e}")
            return {"status": "error", "error": str(e)}
    
    def _format_issues(self, issues: Dict[str, int]) -> str:
        """Format issues for prompt."""
        lines = []
        for issue, count in issues.items():
            if count > 0:
                lines.append(f"- {issue.replace('_', ' ').title()}: {count} occurrences")
        return "\n".join(lines) if lines else "No major issues detected"