"""Twilio webhook handlers."""
import logging
from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from sqlalchemy.orm import Session

from src.services.voice_service import VoiceService
from src.services.analytics_service import AnalyticsService
from src.models import MessageRole, ConversationStatus
from src.database import get_db
from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
voice_service = VoiceService()
analytics_service = AnalyticsService()


@router.post("/twilio/voice")
async def handle_incoming_call(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle incoming Twilio voice call."""
    logger.info(f"Incoming call: {CallSid} from {From} to {To}")
    
    # Normalize phone number - ensure it starts with +
    phone_number = From.strip()
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number.lstrip('+')
    
    # Create conversation in database
    try:
        conversation = analytics_service.create_conversation(
            db=db,
            call_sid=CallSid,
            phone_number=phone_number
        )
        logger.info(f"Created conversation: {conversation.id}")
        
        # Log initial system message
        analytics_service.log_message(
            db=db,
            conversation_id=conversation.id,
            role=MessageRole.SYSTEM,
            content="Call started"
        )
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
    
    # Create TwiML response
    response = VoiceResponse()
    response.say("Hello, I'm your career advisor assistant. How can I help you today?")
    
    # Start gathering speech
    gather = Gather(
        input='speech',
        action='/webhooks/twilio/process-speech',
        method='POST',
        speechTimeout='auto',
        timeout=5
    )
    gather.pause(length=1)
    response.append(gather)
    
    response.say("I didn't hear anything. Please tell me how I can help you.")
    
    return Response(content=str(response), media_type="application/xml")


@router.post("/twilio/process-speech")
async def process_speech(
    CallSid: str = Form(...),
    SpeechResult: str = Form(None),
    db: Session = Depends(get_db)
):
    """Process speech input from Twilio."""
    logger.info(f"Processing speech for {CallSid}: {SpeechResult}")
    
    # Get conversation
    conversation = analytics_service.get_conversation_by_call_sid(db, CallSid)
    
    if not conversation:
        logger.error(f"Conversation not found for CallSid: {CallSid}")
        response = VoiceResponse()
        response.say("Sorry, there was an error. Please try again.")
        return Response(content=str(response), media_type="application/xml")
    
    # Log user message
    if SpeechResult:
        analytics_service.log_message(
            db=db,
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=SpeechResult
        )
    
    # Get AI response with conversation context
    try:
        ai_response = await voice_service.process_user_input(
            user_input=SpeechResult or "",
            conversation_id=str(conversation.id),
            db=db
        )
        
        # Log assistant message
        analytics_service.log_message(
            db=db,
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=ai_response
        )
        
        # Create TwiML response
        response = VoiceResponse()
        response.say(ai_response)
        
        # Continue listening
        gather = Gather(
            input='speech',
            action='/webhooks/twilio/process-speech',
            method='POST',
            speechTimeout='auto',
            timeout=5
        )
        gather.pause(length=1)
        response.append(gather)
        
        # Fallback if no speech detected
        response.say("Are you still there? Say goodbye to end the call, or ask me another question.")
        
        return Response(content=str(response), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing speech: {e}")
        response = VoiceResponse()
        response.say("Sorry, I encountered an error. Please try again.")
        return Response(content=str(response), media_type="application/xml")


@router.post("/twilio/status")
async def handle_call_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle call status updates from Twilio."""
    logger.info(f"Call status update: {CallSid} - {CallStatus}")
    
    try:
        # If call is completed, end the conversation
        if CallStatus in ['completed', 'failed', 'busy', 'no-answer']:
            status = ConversationStatus.COMPLETED if CallStatus == 'completed' else ConversationStatus.FAILED
            
            conversation = analytics_service.end_conversation(
                db=db,
                call_sid=CallSid,
                status=status
            )
            
            if conversation:
                # Log system message
                analytics_service.log_message(
                    db=db,
                    conversation_id=conversation.id,
                    role=MessageRole.SYSTEM,
                    content=f"Call ended: {CallStatus}"
                )
                logger.info(f"Ended conversation {conversation.id} with status {status}")
            else:
                logger.warning(f"Conversation not found for CallSid: {CallSid}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error handling call status: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/twilio/recording")
async def handle_recording(
    CallSid: str = Form(...),
    RecordingUrl: str = Form(...),
    RecordingDuration: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle recording completion from Twilio."""
    logger.info(f"Recording ready for {CallSid}: {RecordingUrl}")
    
    try:
        conversation = analytics_service.get_conversation_by_call_sid(db, CallSid)
        
        if conversation:
            # Log recording info
            analytics_service.log_message(
                db=db,
                conversation_id=conversation.id,
                role=MessageRole.SYSTEM,
                content=f"Recording available",
                extra_data=f'{{"url": "{RecordingUrl}", "duration": "{RecordingDuration}"}}'
            )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error handling recording: {e}")
        return {"status": "error", "message": str(e)}