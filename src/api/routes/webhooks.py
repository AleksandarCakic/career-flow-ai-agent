"""Twilio webhook handlers."""
import logging
from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from twilio.rest import Client
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

# Initialize Twilio client
twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)


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
        
        # Check if this is a returning user
        from src.models import User
        user = db.query(User).filter(User.phone_number == phone_number).first()
        
        # Create greeting prompt based on user status
        if user is not None and getattr(user, "first_name", None):
            # Returning user with name
            greeting_prompt = f"[CALL START - This is a RETURNING user named {user.first_name}. Greet them warmly by name!]"
        else:
            # New user or returning without name - treat the same
            greeting_prompt = "[CALL START - Give standard greeting and ask what brings them to Career Flow.]"
        
        # Get initial greeting based on user context
        initial_greeting = await voice_service.process_user_input(
            user_input=greeting_prompt,
            conversation_id=str(conversation.id),
            db=db,
            phone_number=phone_number
        )
        
        # Log system message
        analytics_service.log_message(
            db=db,
            conversation_id=str(conversation.id),
            role=MessageRole.SYSTEM,
            content="Call started"
        )
        
        # Log AI greeting
        analytics_service.log_message(
            db=db,
            conversation_id=str(conversation.id),
            role=MessageRole.ASSISTANT,
            content=initial_greeting
        )
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        initial_greeting = "Hi, thanks for calling Career Flow, my name is Mica. How can I help you today?"
    
    # Create TwiML response
    response = VoiceResponse()
    response.say(initial_greeting, voice='Polly.Joanna')
    
    # Start gathering speech
    gather = Gather(
        input='speech',
        action='/webhooks/twilio/process-speech',
        method='POST',
        speechTimeout='auto',
        timeout=3,
        language='en-US'
    )
    gather.pause(length=1)
    response.append(gather)
    
    response.say("Sorry, I didn't catch that. What can I help you with?", voice='Polly.Joanna')
    
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
        response.say("Sorry, there was an error. Please try again.", voice='Polly.Joanna')
        return Response(content=str(response), media_type="application/xml")
    
    # Log user message
    if SpeechResult:
        analytics_service.log_message(
            db=db,
            conversation_id=str(conversation.id),
            role=MessageRole.USER,
            content=SpeechResult
        )
    
    # Check if user wants to speak to human
    wants_human = False
    if SpeechResult:
        human_keywords = [
            "speak to", "talk to", "connect me", "transfer", "human",
            "real person", "someone", "alex", "coach"
        ]
        wants_human = any(keyword in SpeechResult.lower() for keyword in human_keywords)
    
    # Get AI response with conversation context
    try:
        ai_response = await voice_service.process_user_input(
            user_input=SpeechResult or "",
            conversation_id=str(conversation.id),
            db=db,
            phone_number=str(conversation.phone_number)
        )
        
        # Log assistant message
        analytics_service.log_message(
            db=db,
            conversation_id=str(conversation.id),
            role=MessageRole.ASSISTANT,
            content=ai_response
        )
        
        # Check if AI is trying to transfer (look for specific phrases)
        attempting_transfer = any(phrase in ai_response.lower() for phrase in [
            "connect you with alex",
            "try to connect",
            "let me try",
            "connecting you"
        ])
        
        # Create TwiML response
        response = VoiceResponse()
        
        if attempting_transfer and wants_human:
            try:
                # AI said it would transfer - actually attempt it
                response.say("Connecting you now.", voice='Polly.Joanna')
                
                # Attempt to dial Alex (add Alex's number to config)
                dial = Dial(
                    timeout=20,
                    action='/webhooks/twilio/transfer-status',
                    method='POST'
                )
                dial.number(settings.alex_phone_number)
                response.append(dial)
                
                # Log transfer attempt
                analytics_service.log_message(
                    db=db,
                    conversation_id=str(conversation.id),
                    role=MessageRole.SYSTEM,
                    content=f"Transfer attempted to Alex: {settings.alex_phone_number}"
                )
            except Exception as transfer_error:
                logger.error(f"Transfer failed: {transfer_error}")
                response.say("Sorry, I'm having trouble connecting the call. Can I help you with anything else?", voice='Polly.Joanna')
        else:
            # Normal conversation flow
            response.say(ai_response, voice='Polly.Joanna')
        
        # Continue listening
        gather = Gather(
            input='speech',
            action='/webhooks/twilio/process-speech',
            method='POST',
            speechTimeout='auto',
            timeout=3,
            language='en-US'
        )
        gather.pause(length=1)
        response.append(gather)
        
        # Fallback if no speech detected
        response.say("Still there?", voice='Polly.Joanna')
        
        return Response(content=str(response), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing speech: {e}")
        response = VoiceResponse()
        response.say("Sorry, I'm having a technical issue. Can you try that again?", voice='Polly.Joanna')
        return Response(content=str(response), media_type="application/xml")


@router.post("/twilio/transfer-status")
async def handle_transfer_status(
    CallSid: str = Form(...),
    DialCallStatus: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle call transfer status."""
    logger.info(f"Transfer status for {CallSid}: {DialCallStatus}")
    
    conversation = analytics_service.get_conversation_by_call_sid(db, CallSid)
    if conversation:
        analytics_service.log_message(
            db=db,
            conversation_id=str(conversation.id),
            role=MessageRole.SYSTEM,
            content=f"Transfer result: {DialCallStatus}"
        )
    
    return Response(content="<Response></Response>", media_type="application/xml")


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
                    conversation_id=str(conversation.id),
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
                conversation_id=str(conversation.id),
                role=MessageRole.SYSTEM,
                content=f"Recording available",
                extra_data=f'{{"url": "{RecordingUrl}", "duration": "{RecordingDuration}"}}'
            )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error handling recording: {e}")
        return {"status": "error", "message": str(e)}