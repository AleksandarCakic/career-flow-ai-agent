"""Twilio webhook handlers."""
from fastapi import APIRouter, Form, Response, Depends
from twilio.twiml.voice_response import VoiceResponse, Gather
from sqlalchemy.orm import Session
from src.services.ai_service import AIService
from src.services.conversation_memory_service import get_memory_service
from src.services.analytics_service import AnalyticsService
from src.models.conversation import MessageRole, ConversationStatus
from src.database import get_db_session
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/twilio/voice")
async def voice_webhook(
    CallSid: str = Form(None),
    From: str = Form(None),
    db: Session = Depends(get_db_session)
):
    """Handle incoming Twilio voice calls."""
    logger.info(f"Incoming call from {From}, CallSid: {CallSid}")
    
    # Create conversation record in database
    analytics = AnalyticsService()
    conversation = analytics.create_conversation(db, CallSid, From)
    
    # Clean up old conversations in memory
    memory_service = get_memory_service()
    memory_service.cleanup_old_conversations()
    
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/webhooks/twilio/process-speech",
        method="POST",
        speech_timeout="auto",
    )
    
    greeting = "Hello! I'm your career advisor assistant. How can I help you today?"
    gather.say(greeting)
    response.append(gather)
    response.say("I didn't receive any input. Goodbye!")
    
    # Log system message
    analytics.log_message(
        db,
        str(conversation.id),
        MessageRole.SYSTEM,
        greeting
    )

    return Response(content=str(response), media_type="application/xml")


@router.post("/twilio/process-speech")
async def process_speech(
    SpeechResult: str = Form(None),
    CallSid: str = Form(None),
    db: Session = Depends(get_db_session)
):
    """Process speech input from Twilio and respond with AI."""
    logger.info(f"Processing speech for CallSid {CallSid}: {SpeechResult}")
    response = VoiceResponse()
    
    memory_service = get_memory_service()
    analytics = AnalyticsService()
    
    # Get conversation from database
    conversation = analytics.get_conversation_by_call_sid(db, CallSid)
    if not conversation:
        logger.error(f"Conversation not found for call {CallSid}")
        response.say("Sorry, I'm having technical difficulties. Please try again later.")
        return Response(content=str(response), media_type="application/xml")

    if SpeechResult:
        # Check for goodbye/end keywords
        goodbye_keywords = ["goodbye", "bye", "end call", "hang up", "that's all", "thank you bye"]
        if any(keyword in SpeechResult.lower() for keyword in goodbye_keywords):
            farewell = "Thank you for using our career advisor service. Have a great day! Goodbye!"
            response.say(farewell)
            response.hangup()
            
            # Log user and assistant messages
            analytics.log_message(db, str(conversation.id), MessageRole.USER, SpeechResult)
            analytics.log_message(db, str(conversation.id), MessageRole.ASSISTANT, farewell)
            
            # End conversation
            analytics.end_conversation(db, CallSid, ConversationStatus.COMPLETED)
            
            # Clear memory
            memory_service.clear_history(CallSid)
            
            return Response(content=str(response), media_type="application/xml")
        
        try:
            # Store user message in memory
            memory_service.store_message(CallSid, "user", SpeechResult)
            
            # Log to database
            analytics.log_message(db, str(conversation.id), MessageRole.USER, SpeechResult)
            
            # Get conversation history
            conversation_history = memory_service.format_for_openai(
                CallSid,
                system_prompt="You are a helpful career advisor assistant. Keep responses concise and conversational for a phone call. End with a follow-up question to continue the conversation."
            )
            
            # Generate AI response
            ai_service = AIService()
            ai_response = ai_service.generate_response(
                SpeechResult,
                conversation_history=conversation_history
            )
            
            # Store assistant response in memory
            memory_service.store_message(CallSid, "assistant", ai_response)
            
            # Log to database
            analytics.log_message(db, str(conversation.id), MessageRole.ASSISTANT, ai_response)
            
            response.say(ai_response)
            logger.info(f"AI response generated for CallSid {CallSid}")
            
            # Add gather for continuation
            gather = Gather(
                input="speech",
                action="/webhooks/twilio/process-speech",
                method="POST",
                speech_timeout="auto",
                timeout=5
            )
            gather.pause(length=1)
            response.append(gather)
            
            response.say("Are you still there? Say goodbye to end the call, or ask me another question.")
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            response.say("I'm sorry, I'm having trouble processing that right now. Please try again.")
    else:
        response.say("I didn't catch that. Please try again.")
        gather = Gather(
            input="speech",
            action="/webhooks/twilio/process-speech",
            method="POST",
            speech_timeout="auto",
        )
        response.append(gather)

    return Response(content=str(response), media_type="application/xml")


@router.post("/twilio/call-status")
async def call_status(
    CallSid: str = Form(None),
    CallStatus: str = Form(None),
    db: Session = Depends(get_db_session)
):
    """Handle call status updates from Twilio."""
    logger.info(f"Call status update for {CallSid}: {CallStatus}")
    
    if CallStatus in ["completed", "busy", "no-answer", "canceled", "failed"]:
        # Determine status
        status_map = {
            "completed": ConversationStatus.COMPLETED,
            "busy": ConversationStatus.FAILED,
            "no-answer": ConversationStatus.ABANDONED,
            "canceled": ConversationStatus.ABANDONED,
            "failed": ConversationStatus.FAILED
        }
        
        # End conversation in database
        analytics = AnalyticsService()
        analytics.end_conversation(db, CallSid, status_map.get(CallStatus, ConversationStatus.COMPLETED))
        
        # Clear memory
        memory_service = get_memory_service()
        memory_service.clear_history(CallSid)
        
        logger.info(f"Cleaned up conversation for ended call {CallSid}")
    
    return Response(content="OK", media_type="text/plain")