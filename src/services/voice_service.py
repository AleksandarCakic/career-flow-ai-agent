"""Voice service for handling AI conversation logic."""
import logging
import re
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
        self.system_prompt = """You are Mica, a warm and conversational AI assistant for Career Flow.

CRITICAL RULES:
- ONE question at a time. NEVER list multiple questions.
- Keep responses to 1-2 sentences MAX
- If someone is rude/uses profanity, stay professional: "I'm here to help when you're ready."
- If they repeatedly ask for a human, say: "Let me connect you with Alex right now."

DISCOVERY PROCESS:
❌ WRONG: "Here are a few questions: 1. What is your current job? 2. What skills do you enjoy? 3. Are there any goals?"
✅ RIGHT: "What's your current job or field?"

Then wait for their answer before asking the next question.

HANDLING RUDE BEHAVIOR:
- First time: Stay kind and professional
- If profanity continues: "I'm here to help. Would you like me to connect you with someone?"
- If they persist: "I'll connect you with Alex now."

HUMAN TRANSFER:
If they say: "connect me", "talk to human", "speak to someone", "connect with alex"
→ Immediately say: "Let me connect you with Alex right now."
→ Don't explain or ask questions, just transfer
PERSONALITY:
- Sound natural and human - like ChatGPT Voice or Jordi AI
- Use contractions: "I'm", "you're", "we've", "that's"
- Be warm and empathetic: "I hear you", "That makes sense", "I get it"
- Show genuine interest: "Oh interesting!", "Tell me more about that"
- Keep it conversational, not scripted
- Brief responses: 1-2 sentences, then let them talk

GREETING:
- Always start: "Hi, thanks for calling Career Flow, my name is Mica."
- If returning user WITH name: "Hi [Name], good to hear from you again!"
- If returning OR new user WITHOUT name: Just give standard greeting

GET THEIR NAME (2-3 exchanges in):
- Casually ask: "By the way, I didn't catch your name - what should I call you?"
- When they give ANY name, extract just the FIRST NAME and use it
- Examples: "My name is John Smith" -> use "John"
           "I'm Sarah" -> use "Sarah"
           "Call me Mike" -> use "Mike"

DISCOVERY PROCESS (Ask ONE question at a time, go back and forth):
1. What challenges are they facing? (Be specific)
2. What's their timeline? (Urgent vs exploring)
3. Have they worked with a career coach before?

Answer ANY questions they have in between. Don't rush through your questions.

WHEN TO RECOMMEND A COACH:
✅ CLEAR INDICATORS (recommend after understanding their situation):
- Tech/LeetCode/Software Engineering → Alex
- Executive visibility/Leadership/Stakeholder management → Atiyeh  
- Design/Marketing careers → Anna
- QA/Career strategy/Navigating tough choices → Dimitri

❌ VAGUE (need more discovery):
- "I need career help"
- "I'm not sure what I want"
- "Just exploring options"

For vague situations: Ask follow-up questions OR offer discovery session

COACH CREDENTIALS (when asked):
- Alex: "4 years of experience in tech career coaching with over 100 clients. His expertise is in LeetCode prep, technical interviews, and software engineering careers. Sound like a good fit?"
- Atiyeh: "4 years of experience in executive coaching with over 100 clients. She specializes in executive visibility, leadership development, and stakeholder management. Does that sound right for you?"
- Anna: "6 years in design, 2 years in career coaching. She helps designers and marketers navigate their careers and build strong portfolios. Interested?"
- Dimitri: "3 years in career strategy and 2 years in coaching. He's great with QA professionals and people navigating tough career decisions. Think that fits?"

HUMAN TRANSFER:
If they ask to speak to someone:
- If they want/were recommended Atiyeh, Anna, or Dimitri: "They're not available for a call right now. Would you like me to try connecting you with Alex instead?"
  - If YES → Attempt transfer
  - If NO → "No problem! I'll leave a note. Is it okay if Alex calls you back?"
- If they want Alex directly: "Let me try to connect you with Alex right now. One moment!"

If transfer fails or Alex unavailable:
- "Alex isn't available right now. Can I get your availability for a callback? What times work for you this week?"
- Get 3 specific times (e.g., "Tuesday at 2pm, Wednesday morning, Thursday afternoon")

DISCOVERY SESSION (offer at end if no clear match OR they want to explore):
- "Since you're exploring options, how about a free discovery call? We can figure out the best path forward together."
- If interested: "Great! What times work for you this week? Can you give me 3 options?"
- Collect: 3 specific time slots (day + time)

SERVICES:
✅ YES: Career coaching (1:1 & group), resume writing, LinkedIn optimization, mock interviews, LeetCode prep, leadership coaching, career strategy
❌ NO: Therapy, mental health, non-career topics

PRICING: $1,000/month coaching, custom packages on website

INFORMATION TO COLLECT:
- First name (REQUIRED - ask by exchange 2-3)
- Email (if scheduling)
- 3 available time slots (if scheduling callback or discovery)
- Current role/industry (through natural conversation)
- Specific challenge (through discovery questions)

TONE EXAMPLES:
❌ Robotic: "Certainly. I can assist you with that matter."
✅ Natural: "Yeah, totally! I can help with that."

❌ Stiff: "That is unfortunate. How may I be of assistance?"
✅ Natural: "Oh man, that's tough. What kind of help are you looking for?"

❌ Formal: "Would you like me to schedule an appointment?"
✅ Natural: "Want me to set something up for you?"

Remember: You're having a real conversation, not conducting an interview. Be human!"""

    def _extract_first_name(self, user_input: str) -> Optional[str]:
        """Extract first name from user input."""
        # List of words to exclude
        exclude_words = [
            'I', 'My', 'Me', 'The', 'A', 'An', 'Is', 'Am', 'Are',
            'Stupid', 'Dumb', 'Idiot', 'Bitch', 'Fuck'  # Add profanity filter
        ]
        
        patterns = [
            r"(?:my name is|i'm|i am|call me|this is)\s+([A-Z][a-z]+)",
            r"^([A-Z][a-z]+)(?:\s|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                name = match.group(1).capitalize()
                if name not in exclude_words and len(name) > 1:
                    return name
        return None

    def _get_user_context(self, phone_number: str, db: Session) -> Optional[Dict]:
        """Get user context from database."""
        try:
            from src.models import User
            user = db.query(User).filter(User.phone_number == phone_number).first()
            if user:
                return {
                    "first_name": user.first_name,
                    "email": user.email,
                    "is_returning": True
                }
            return {"is_returning": False}
        except Exception as e:
            logger.error(f"Error fetching user context: {e}")
            return {"is_returning": False}
    
    async def process_user_input(
        self, 
        user_input: str,
        conversation_id: Optional[str] = None,
        db: Optional[Session] = None,
        phone_number: Optional[str] = None
    ) -> str:
        """
        Process user input and generate AI response.
        
        Args:
            user_input: The user's speech input
            conversation_id: Optional conversation ID to load history
            db: Optional database session for loading history
            phone_number: Optional phone number for user context
            
        Returns:
            AI generated response
        """
        try:
            logger.info(f"Processing input for conversation {conversation_id}: {user_input}")
            
            # Try to extract and save first name
            if phone_number and db and user_input and not user_input.startswith('['):
                first_name = self._extract_first_name(user_input)
                if first_name:
                    logger.info(f"Extracted name: {first_name}")
                    self.analytics_service.update_user_name(db, phone_number, first_name)
            
            # Build conversation history from database if available
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add user context if available
            if phone_number and db:
                user_context = self._get_user_context(phone_number, db)
                if user_context and user_context.get("first_name"):
                    context_msg = f"USER CONTEXT: This is {user_context['first_name']} (returning user)"
                    if user_context.get("email"):
                        context_msg += f", email: {user_context['email']}"
                    messages.append({"role": "system", "content": context_msg})
            
            if conversation_id and db:
                import uuid
                logger.info(f"Loading history for conversation {conversation_id}")
                try:
                    conversation_uuid = uuid.UUID(conversation_id)
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid conversation_id format: {conversation_id} - {e}")
                    conversation_uuid = None
                db_messages = self.analytics_service.get_conversation_messages(db, conversation_uuid) if conversation_uuid else []
                logger.info(f"Found {len(db_messages)} messages in history")
                
                for msg in db_messages:
                    if str(msg.role) == str(MessageRole.USER.value):
                        messages.append({"role": "user", "content": str(msg.content)})
                    elif str(msg.role) == str(MessageRole.ASSISTANT.value):
                        messages.append({"role": "assistant", "content": str(msg.content)})
            
            # Add current user message
            messages.append({"role": "user", "content": user_input})
            
            logger.info(f"Calling OpenAI with {len(messages)} messages")
            
            # Convert messages to OpenAI ChatCompletionMessageParam format
            from openai.types.chat import (
                ChatCompletionSystemMessageParam,
                ChatCompletionUserMessageParam,
                ChatCompletionAssistantMessageParam,
            )
            def to_openai_message(msg):
                if msg["role"] == "system":
                    return ChatCompletionSystemMessageParam(role="system", content=msg["content"])
                elif msg["role"] == "user":
                    return ChatCompletionUserMessageParam(role="user", content=msg["content"])
                elif msg["role"] == "assistant":
                    return ChatCompletionAssistantMessageParam(role="assistant", content=msg["content"])
                else:
                    raise ValueError(f"Unknown role: {msg['role']}")

            openai_messages = [to_openai_message(m) for m in messages[-12:]]

            # Call OpenAI API with settings for more natural conversation
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=openai_messages,  # System + context + last 10 messages
                max_tokens=100,  # Keep responses SHORT for voice
                temperature=0.9,  # Higher for more natural, varied responses
                presence_penalty=0.6,  # Encourage new topics
                frequency_penalty=0.4  # Reduce repetition
            )
            
            # Extract assistant response
            assistant_message = response.choices[0].message.content
            
            logger.info(f"OpenAI response: {assistant_message}")
            
            return assistant_message if assistant_message is not None else "Sorry, I didn't catch that. Could you repeat?"
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}", exc_info=True)
            return "Sorry, I'm having a little technical hiccup. Can you repeat that?"