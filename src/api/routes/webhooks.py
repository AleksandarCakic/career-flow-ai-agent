"""Twilio webhook handlers."""
from fastapi import APIRouter, Form, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from src.services.ai_service import AIService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/twilio/voice")
async def voice_webhook(CallSid: str = Form(None), From: str = Form(None)):
    """Handle incoming Twilio voice calls."""
    logger.info(f"Incoming call from {From}, CallSid: {CallSid}")
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/webhooks/twilio/process-speech",
        method="POST",
        speech_timeout="auto",
    )
    gather.say("Hello! I'm your career advisor assistant. How can I help you today?")
    response.append(gather)
    response.say("I didn't receive any input. Goodbye!")

    return Response(content=str(response), media_type="application/xml")


@router.post("/twilio/process-speech")
async def process_speech(
    SpeechResult: str = Form(None),
    CallSid: str = Form(None),
):
    """Process speech input from Twilio and respond with AI."""
    logger.info(f"Processing speech for CallSid {CallSid}: {SpeechResult}")
    response = VoiceResponse()

    if SpeechResult:
        # Check for goodbye/end keywords
        goodbye_keywords = ["goodbye", "bye", "end call", "hang up", "that's all", "thank you bye"]
        if any(keyword in SpeechResult.lower() for keyword in goodbye_keywords):
            response.say("Thank you for using our career advisor service. Have a great day! Goodbye!")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")
        
        try:
            ai_service = AIService()
            ai_response = ai_service.generate_response(
                SpeechResult,
                system_prompt="You are a helpful career advisor assistant. Keep responses concise and conversational for a phone call. End with a follow-up question to continue the conversation."
            )
            response.say(ai_response)
            logger.info(f"AI response generated for CallSid {CallSid}")
            
            # Add another Gather to continue the conversation
            gather = Gather(
                input="speech",
                action="/webhooks/twilio/process-speech",
                method="POST",
                speech_timeout="auto",
                timeout=5  # Wait 5 seconds for user input
            )
            gather.pause(length=1)  # Brief pause before listening again
            response.append(gather)
            
            response.say("Are you still there? Say goodbye to end the call, or ask me another question.")
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            response.say("I'm sorry, I'm having trouble processing that right now. Please try again.")
    else:
        response.say("I didn't catch that. Please try again.")
        
        # Add gather for retry
        gather = Gather(
            input="speech",
            action="/webhooks/twilio/process-speech",
            method="POST",
            speech_timeout="auto",
        )
        response.append(gather)

    return Response(content=str(response), media_type="application/xml")