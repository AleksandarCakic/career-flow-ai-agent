"""Service for analyzing conversations and generating prompt improvements."""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from openai import OpenAI
from sqlalchemy.orm import Session

from src.models.models import Conversation, Message, ConversationStatus, MessageRole
from src.config import settings
import os

logger = logging.getLogger(__name__)

class PromptOptimizerService:
    """Service for analyzing conversations and optimizing prompts."""
    
    def __init__(self):
        """Initialize the service."""
        api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "openai_api_key", None)
        self.client = OpenAI(api_key=api_key)
        self.reports_dir = Path("analysis_reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    def analyze_conversations(
        self,
        db: Session,
        hours_back: int = 168  # Default: last 7 days
    ) -> Dict:
        """
        Analyze recent conversations and generate recommendations.
        
        Two-phase approach:
        1. Pattern Detection: Find issues using rule-based logic
        2. AI Analysis: Generate specific recommendations
        """
        try:
            # Fetch conversations from specified time period
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            conversations = db.query(Conversation).filter(
                Conversation.started_at >= cutoff_time,
                Conversation.status == ConversationStatus.COMPLETED
            ).all()
            
            if not conversations:
                return {
                    "status": "no_data",
                    "message": f"No conversations found in last {hours_back} hours"
                }
            
            logger.info(f"Analyzing {len(conversations)} conversations")
            
            # Phase 1: Pattern Detection
            issues = self._detect_patterns(conversations, db)
            
            # Phase 2: AI Analysis (only if issues found)
            ai_recommendations = {}
            if any(issues.values()):
                ai_recommendations = self._generate_ai_recommendations(
                    conversations, issues, db
                )
            
            # Generate report
            report = self._generate_report(
                conversations, issues, ai_recommendations, hours_back
            )
            
            # Save report
            self._save_report(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error analyzing conversations: {e}")
            raise
    
    def _detect_patterns(
        self, 
        conversations: List[Conversation],
        db: Session
    ) -> Dict[str, List[Dict]]:
        """
        Phase 1: Detect patterns using rule-based logic.
        Returns dict of issue types with affected conversation details.
        """
        issues = {
            "technical_errors": [],
            "transfer_failures": [],
            "multiple_questions": [],
            "long_conversations": [],
            "name_not_collected": []
        }
        
        for conv in conversations:
            # Get messages for this conversation
            messages = db.query(Message).filter(
                Message.conversation_id == conv.id
            ).all()
            
            if not messages:
                continue
            
            # Separate by role (filter AFTER getting from DB to avoid SQLAlchemy type issues)
            user_messages = [m for m in messages if m.role.value == MessageRole.USER.value]
            assistant_messages = [m for m in messages if m.role.value == MessageRole.ASSISTANT.value]
            system_messages = [m for m in messages if m.role.value == MessageRole.SYSTEM.value]
            total_messages = len(messages)
            
            logger.debug(f"Conv {conv.call_sid}: {total_messages} total messages")
            
            # Check 1: Technical errors
            error_keywords = ["error", "hiccup", "technical", "problem", "issue", 
                            "unintelligible", "didn't catch", "couldn't understand"]
            for msg in messages:
                if any(keyword in msg.content.lower() for keyword in error_keywords):
                    issues["technical_errors"].append({
                        "conversation_id": str(conv.id),
                        "call_sid": conv.call_sid,
                        "message": msg.content,
                        "timestamp": conv.started_at.isoformat()
                    })
                    logger.info(f"Technical error in {conv.call_sid}")
                    break
            
            # Check 2: Transfer failures
            transfer_requested = any(
                "transfer" in m.content.lower() or "connect" in m.content.lower() 
                for m in assistant_messages
            )
            transfer_failed = any(
                "not executed" in m.content.lower() or "failed" in m.content.lower() 
                for m in system_messages
            )
            
            if transfer_requested and transfer_failed:
                issues["transfer_failures"].append({
                    "conversation_id": str(conv.id),
                    "call_sid": conv.call_sid,
                    "system_message": system_messages[0].content if system_messages else "Transfer not executed",
                    "timestamp": conv.started_at.isoformat()
                })
                logger.info(f"Transfer failure in {conv.call_sid}")
            
            # Check 3: Multiple questions (≥3 questions in one message)
            for msg in user_messages:
                question_marks = msg.content.count('?')
                if question_marks >= 3:
                    issues["multiple_questions"].append({
                        "conversation_id": str(conv.id),
                        "call_sid": conv.call_sid,
                        "message": msg.content,
                        "num_questions": question_marks,
                        "timestamp": conv.started_at.isoformat()
                    })
                    logger.info(f"Multiple questions in {conv.call_sid}: {question_marks} questions")
                    break
            
            # Check 4: Long conversations (>10 total messages)
            if total_messages > 10:
                issues["long_conversations"].append({
                    "conversation_id": str(conv.id),
                    "call_sid": conv.call_sid,
                    "num_messages": total_messages,
                    "duration_seconds": conv.duration_seconds,
                    "timestamp": conv.started_at.isoformat()
                })
                logger.info(f"Long conversation: {conv.call_sid} has {total_messages} messages")
            
            # Check 5: Name collection
            name_collected = False
            name_keywords = ["name is", "i'm", "im", "this is", "call me"]
            
            # Check first 3 user messages for name
            for msg in user_messages[:3]:
                content_lower = msg.content.lower()
                
                # Check for name keywords
                if any(kw in content_lower for kw in name_keywords):
                    name_collected = True
                    logger.debug(f"Name collected in {conv.call_sid}: {msg.content}")
                    break
                
                # Check for short name response (1-3 words)
                if len(msg.content.split()) <= 3:
                    # Find corresponding assistant message that came before this user message
                    msg_index = user_messages.index(msg)
                    if msg_index < len(assistant_messages):
                        prev_assistant = assistant_messages[msg_index]
                        if "name" in prev_assistant.content.lower():
                            name_collected = True
                            logger.debug(f"Name collected (short) in {conv.call_sid}: {msg.content}")
                            break
            
            # Check if assistant asked for name
            assistant_asked_name = any(
                "name" in m.content.lower() and "?" in m.content 
                for m in assistant_messages[:2]
            )
            
            # Issue: Assistant asked for name but user didn't provide it AND conversation continued
            if assistant_asked_name and not name_collected and len(user_messages) > 2:
                issues["name_not_collected"].append({
                    "conversation_id": str(conv.id),
                    "call_sid": conv.call_sid,
                    "num_user_messages": len(user_messages),
                    "timestamp": conv.started_at.isoformat()
                })
                logger.info(f"Name not collected in {conv.call_sid} after {len(user_messages)} messages")
        
        # Log summary
        total_issues = sum(len(v) for v in issues.values())
        logger.info(f"Pattern detection complete: {total_issues} total issues found")
        for issue_type, occurrences in issues.items():
            if occurrences:
                logger.info(f"  - {issue_type}: {len(occurrences)}")
        
        return issues
    
    def _generate_ai_recommendations(
        self,
        conversations: List[Conversation],
        issues: Dict[str, List[Dict]],
        db: Session
    ) -> Dict:
        """
        Phase 2: Use GPT-4o-mini to generate specific recommendations.
        """
        # Build context for AI
        issue_summary = []
        for issue_type, occurrences in issues.items():
            if occurrences:
                issue_summary.append(
                    f"- {issue_type.replace('_', ' ').title()}: {len(occurrences)} occurrence(s)"
                )
        
        if not issue_summary:
            return {
                "critical_issues": [],
                "recommendations": [],
                "confidence": "N/A"
            }
        
        # Sample conversations with issues
        sample_conversations = []
        for conv in conversations[:5]:
            messages = db.query(Message).filter(
                Message.conversation_id == conv.id
            ).all()
            
            transcript = []
            for msg in messages:
                role = "User" if msg.role.value == MessageRole.USER.value else "Mica" if msg.role.value == MessageRole.ASSISTANT.value else "System"
                transcript.append(f"{role}: {msg.content}")
            
            sample_conversations.append({
                "call_sid": conv.call_sid,
                "transcript": "\n".join(transcript)
            })
        
        # Prepare prompt for GPT-4o-mini
        prompt = f"""You are an expert AI conversation analyst. Analyze these phone conversations with Mica, an AI career coach.

DETECTED ISSUES:
{chr(10).join(issue_summary)}

SAMPLE CONVERSATIONS:
{json.dumps(sample_conversations, indent=2)}

Based on the issues detected, provide:
1. Critical issues that need immediate attention (list issue types)
2. Specific, actionable recommendations for each issue type
3. Rationale for why each change will improve the conversation

Format your response as JSON:
{{
    "critical_issues": ["issue1", "issue2"],
    "recommendations": [
        {{
            "issue": "issue_type",
            "suggestion": "specific actionable fix",
            "rationale": "why this helps"
        }}
    ],
    "confidence": "HIGH/MEDIUM/LOW"
}}

Focus on improving:
- User experience and conversation flow
- Information collection efficiency  
- Error handling and recovery
- Transfer success rates
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content is not None:
                recommendations = json.loads(content)
                logger.info(f"AI recommendations generated: {len(recommendations.get('recommendations', []))} items")
                return recommendations
            else:
                logger.error("AI response content is None")
                return {
                    "critical_issues": [],
                    "recommendations": [],
                    "confidence": "LOW",
                    "error": "AI response content is None"
                }
            
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {e}")
            return {
                "critical_issues": [],
                "recommendations": [],
                "confidence": "LOW",
                "error": str(e)
            }
    
    def _generate_report(
        self,
        conversations: List[Conversation],
        issues: Dict[str, List[Dict]],
        ai_recommendations: Dict,
        hours_back: int
    ) -> Dict:
        """Generate comprehensive analysis report."""
        # Count issues
        issue_counts = {
            issue_type: len(occurrences) 
            for issue_type, occurrences in issues.items()
        }
        
        # Sample conversations
        sample_convos = []
        for conv in conversations[:10]:
            sample_convos.append({
                "call_sid": conv.call_sid,
                "phone_number": conv.phone_number,
                "duration_seconds": conv.duration_seconds,
                "started_at": conv.started_at.isoformat(),
                "status": conv.status.value
            })
        
        report = {
            "status": "analyzed",
            "timestamp": datetime.now().isoformat(),
            "analysis_period": {
                "hours_back": hours_back,
                "start_time": (datetime.now() - timedelta(hours=hours_back)).isoformat()
            },
            "summary": {
                "total_conversations": len(conversations),
                "issues_found": issue_counts,
                "sample_conversations": sample_convos
            },
            "issues": issues,
            "ai_recommendations": ai_recommendations
        }
        
        return report
    
    def _save_report(self, report: Dict) -> None:
        """Save report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.reports_dir / f"report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, indent=2, fp=f)
        
        logger.info(f"Report saved to {filename}")