"""Twilio webhook handlers."""
from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook/twilio/voice")
async def handle_voice_call(request: Request):
    """Handle incoming voice calls from Twilio."""
    # Get form data from Twilio
    form_data = await request.form()
    
    # Log the incoming call
    caller = form_data.get("From", "Unknown")
    call_sid = form_data.get("CallSid", "Unknown")
    logger.info(f"Incoming call from {caller}, CallSid: {call_sid}")
    
    # Create Twilio response
    response = VoiceResponse()
    
    # Greet the caller
    response.say(
        "Hello! I'm Mica, your career guidance assistant. "
        "I'm here to help you explore your career options. "
        "Let's have a conversation about your work preferences and goals.",
        voice="Polly.Matthew",  # Male voice
        language="en-US"
    )
    
    # Pause briefly
    response.pause(length=1)
    
    # Ask first question
    gather = Gather(
        input="speech",
        action="/webhook/twilio/process-speech",
        method="POST",
        speech_timeout="auto",
        language="en-US"
    )
    gather.say(
        "To start, tell me about what you love most about your current work. "
        "What gets you excited or energized?",
        voice="Polly.Matthew",
        language="en-US"
    )
    response.append(gather)
    
    # If no input, prompt again
    response.say(
        "I didn't hear anything. Please try again.",
        voice="Polly.Matthew",
        language="en-US"
    )
    
    return Response(content=str(response), media_type="application/xml")


@router.post("/webhook/twilio/process-speech")
async def process_speech(
    request: Request,
    SpeechResult: str = Form(None),
    CallSid: str = Form(None)
):
    """Process speech input from caller."""
    logger.info(f"Speech received for CallSid {CallSid}: {SpeechResult}")
    
    # Create response
    response = VoiceResponse()
    
    if SpeechResult:
        # Acknowledge the response
        response.say(
            f"Thank you for sharing that. I heard you say: {SpeechResult}. "
            "This is very helpful information.",
            voice="Polly.Matthew",
            language="en-US"
        )
    else:
        response.say(
            "I didn't catch that. Let's try again.",
            voice="Polly.Matthew",
            language="en-US"
        )
    
    # End call for now (we'll add more conversation flow later)
    response.say(
        "Thank you for talking with me today. Goodbye!",
        voice="Polly.Matthew",
        language="en-US"
    )
    response.hangup()
    
    return Response(content=str(response), media_type="application/xml")