from datetime import datetime, timezone
import logging
import os
from typing import Optional
import uuid
import json

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from app.core.scheduler import scheduler
from app.services.twilio_service import TwilioService
from app.core.db import SessionLocal
from app.models import CallSession, CallInteraction

logger = logging.getLogger(__name__)

# Initialize real Twilio service
twilio_service = TwilioService()

router = APIRouter()

class CallRequest(BaseModel):
    to: str
    message: str
    schedule: Optional[str] = None  # cron string or ISO datetime (UTC)
    voice_id: Optional[str] = "Zdsf4NBMlHR5zJJ72y9q"

    @field_validator("to")
    @classmethod
    def validate_phone_number(cls, v):
        if not v or not v.strip():
            raise ValueError("Phone number is required")
        return v.strip()

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("Message is required")
        return v.strip()

class CallResponse(BaseModel):
    success: bool
    status: str
    detail: str
    call_sid: Optional[str] = None
    audio_url: Optional[str] = None
    scheduled_time: Optional[str] = None

def _parse_schedule(schedule_str: str) -> Optional[datetime]:
    """Parse schedule string into datetime."""
    try:
        # Try parsing as ISO datetime
        parsed_time = datetime.fromisoformat(schedule_str.replace('Z', '+00:00'))
        if parsed_time.tzinfo is None:
            parsed_time = parsed_time.replace(tzinfo=timezone.utc)
        
        # Check if the time is in the future
        if parsed_time <= datetime.now(timezone.utc):
            raise ValueError("Schedule time must be in the future")
        
        return parsed_time
    except ValueError as e:
        logger.error(f"Invalid schedule format: {e}")
        return None

def _job_func(to_number: str, message: str, voice_id: str):
    try:
        result = twilio_service.make_call(to_number, message, voice_id)
        if not result["success"]:
            logger.error(f"Scheduled call failed: {result['error']}")
    except Exception as exc:
        logger.exception("Scheduled call failed: %s", exc)

@router.post("/make-call")
async def make_call(request: CallRequest):
    """Make a call immediately or schedule it."""
    try:
        if request.schedule:
            # Schedule the call
            parsed_time = _parse_schedule(request.schedule)
            if not parsed_time:
                raise HTTPException(status_code=400, detail="Invalid schedule format")
            job_id = f"call_{datetime.now().timestamp()}"
            scheduler.add_job(
                func=twilio_service.make_call,
                trigger=DateTrigger(run_date=parsed_time),
                args=[request.to, request.message, request.voice_id],
                id=job_id,
                replace_existing=True
            )
            logger.info(f"Call scheduled for {parsed_time}")
            return {"status": "scheduled", "job_id": job_id, "scheduled_time": parsed_time.isoformat()}
        else:
            # Make immediate call
            result = twilio_service.make_call(request.to, request.message, request.voice_id)
            if result["success"]:
                logger.info(f"Call initiated: {result['call_sid']}")
                # --- DB LOGIC START ---
                db = SessionLocal()
                try:
                    # Create CallSession for this call
                    session_obj = CallSession(
                        id=str(uuid.uuid4()),
                        call_sid=result["call_sid"],
                        twilio_call_sid=result["call_sid"],
                        from_number=result.get("from", ""),
                        to_number=result.get("to", request.to),
                        status=result.get("status", "initiated"),
                        initial_message=request.message,
                        voice_id=request.voice_id,
                    )
                    db.add(session_obj)
                    db.commit()
                except Exception as db_exc:
                    logger.error(f"DB error saving call session: {db_exc}")
                    db.rollback()
                finally:
                    db.close()
                # --- DB LOGIC END ---
                return {"status": "initiated", "call_sid": result["call_sid"]}
            else:
                logger.error(f"Call failed: {result['error']}")
                raise HTTPException(status_code=500, detail=result["error"])
    except Exception as e:
        logger.error(f"Error making call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve local audio files generated by ElevenLabs"""
    audio_dir = "/tmp/tts_audio"
    filepath = os.path.join(audio_dir, filename)
    logger.info(f"[AUDIO ENDPOINT] Request for audio file: {filepath}")
    if not os.path.exists(filepath):
        logger.error(f"[AUDIO ENDPOINT] File not found: {filepath}")
        raise HTTPException(status_code=404, detail="Audio file not found")
    logger.info(f"[AUDIO ENDPOINT] Serving audio file: {filepath}")
    return FileResponse(filepath, media_type="audio/mpeg")

@router.get("/twiml")
async def get_twiml(request: Request):
    """Webhook endpoint for Twilio to fetch TwiML instructions."""
    try:
        # Get parameters from the request
        to_number = request.query_params.get("To")
        message = request.query_params.get("Message", "Hello from Auto-Caller!")
        audio_file = request.query_params.get("AudioFile")
        
        logger.info(f"[TWIML] Request for call to {to_number}, audio_file: {audio_file}")
        
        if audio_file:
            # Use ElevenLabs audio file
            audio_url = f"http://localhost:8000/api/calls/audio/{audio_file}"
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
</Response>'''
            logger.info(f"[TWIML] Using ElevenLabs audio: {audio_url}")
        else:
            # Fallback to Twilio TTS
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{message}</Say>
</Response>'''
            logger.info(f"[TWIML] Using Twilio TTS fallback for message: {message}")
        
        logger.info(f"[TWIML] Generated TwiML for call to {to_number}")
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error generating TwiML: {e}")
        # Return a simple error TwiML
        error_twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Sorry, there was an error processing your call.</Say>
</Response>'''
        return Response(content=error_twiml, media_type="application/xml")

@router.get("/list")
async def list_calls():
    """List recent calls."""
    try:
        result = twilio_service.list_calls()
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except Exception as e:
        logger.error(f"Error listing calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{call_sid}")
async def get_call_status(call_sid: str):
    """Get the status of a specific call."""
    try:
        result = twilio_service.get_call_status(call_sid)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except Exception as e:
        logger.error(f"Error getting call status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/handle-speech")
async def handle_speech(request: Request):
    """Handle speech input from interactive calls - optimized for 300k users."""
    try:
        form_data = await request.form()
        speech_result = form_data.get("SpeechResult", "")
        confidence = form_data.get("Confidence", "0")
        call_sid = form_data.get("CallSid", "")
        logger.info(f"Processing speech for call {call_sid}: '{speech_result}' (confidence: {confidence})")
        # --- DB LOGIC START ---
        db = SessionLocal()
        try:
            # Find or create CallSession
            session_obj = db.query(CallSession).filter_by(call_sid=call_sid).first()
            if not session_obj:
                session_obj = CallSession(
                    id=str(uuid.uuid4()),
                    call_sid=call_sid,
                    twilio_call_sid=call_sid,
                    from_number="",  # Optionally extract from form_data
                    to_number="",    # Optionally extract from form_data
                    status="in_progress",
                )
                db.add(session_obj)
                db.commit()
                db.refresh(session_obj)
            # Find next sequence number
            seq = db.query(CallInteraction).filter_by(call_session_id=session_obj.id).count() + 1
            # Create CallInteraction
            interaction = CallInteraction(
                id=str(uuid.uuid4()),
                call_session_id=session_obj.id,
                interaction_type="speech",
                sequence_number=seq,
                speech_result=speech_result,
                speech_confidence=float(confidence) if confidence else None,
            )
            db.add(interaction)
            db.commit()
        except Exception as db_exc:
            logger.error(f"DB error saving call interaction: {db_exc}")
            db.rollback()
        finally:
            db.close()
        # --- DB LOGIC END ---
        # --- TEMP FILE LOGIC START ---
        try:
            log_obj = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "call_sid": call_sid,
                "type": "speech",
                "transcript": speech_result,
                "audio_url": None,
                "confidence": float(confidence) if confidence else None,
            }
            with open("/tmp/call_interactions_log.jsonl", "a") as f:
                f.write(json.dumps(log_obj) + "\n")
        except Exception as file_exc:
            logger.error(f"Failed to write call interaction to temp file: {file_exc}")
        # --- TEMP FILE LOGIC END ---
        response_message, end_call = _process_speech_input(speech_result.lower())
        if end_call:
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n    <Say speed="slow">{response_message}</Say>\n    <Hangup/>\n</Response>"""
        else:
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n    <Gather input="speech" action="/api/calls/handle-speech" method="POST" speechTimeout="10" enhanced="true" timeout="45">\n        <Say speed="slow">{response_message}</Say>\n    </Gather>\n    <Say speed="slow">I didn't hear anything. Let me try again.</Say>\n    <Gather input="speech" action="/api/calls/handle-speech" method="POST" speechTimeout="10" enhanced="true" timeout="45">\n        <Say speed="slow">Please speak now. I'm here to help!</Say>\n    </Gather>\n    <Say speed="slow">Thank you for calling. Have a great day!</Say>\n    <Hangup/>\n</Response>"""
        logger.info(f"Generated response for call {call_sid}: {response_message[:50]}...")
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        logger.error(f"Error handling speech for call {call_sid}: {e}")
        error_twiml = '''<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n    <Say speed="slow">Sorry, I didn't understand that. Please try again.</Say>\n    <Gather input="speech" action="/api/calls/handle-speech" method="POST" speechTimeout="10" enhanced="true" timeout="45">\n        <Say speed="slow">What would you like me to help you with?</Say>\n    </Gather>\n    <Say speed="slow">Thank you for calling. Goodbye!</Say>\n    <Hangup/>\n</Response>'''
        return Response(content=error_twiml, media_type="application/xml")

@router.post("/handle-recording")
async def handle_recording(request: Request):
    """Handle recording from interactive calls - store audio and continue conversation."""
    try:
        form_data = await request.form()
        recording_url = form_data.get("RecordingUrl", "")
        recording_sid = form_data.get("RecordingSid", "")
        call_sid = form_data.get("CallSid", "")
        recording_duration = form_data.get("RecordingDuration", "0")
        logger.info(f"Processing recording for call {call_sid}: {recording_sid}, duration: {recording_duration}s")
        s3_recording_url = twilio_service.download_and_store_recording(recording_url, call_sid)
        whisper_transcript = None
        if s3_recording_url:
            whisper_transcript = twilio_service.transcribe_audio_with_whisper(recording_url)
        logger.info(f"Recording stored: {s3_recording_url}")
        logger.info(f"Whisper transcript: {whisper_transcript}")
        # --- DB LOGIC START ---
        db = SessionLocal()
        try:
            # Find or create CallSession
            session_obj = db.query(CallSession).filter_by(call_sid=call_sid).first()
            if not session_obj:
                session_obj = CallSession(
                    id=str(uuid.uuid4()),
                    call_sid=call_sid,
                    twilio_call_sid=call_sid,
                    from_number="",  # Optionally extract from form_data
                    to_number="",    # Optionally extract from form_data
                    status="in_progress",
                )
                db.add(session_obj)
                db.commit()
                db.refresh(session_obj)
            # Find next sequence number
            seq = db.query(CallInteraction).filter_by(call_session_id=session_obj.id).count() + 1
            # Create CallInteraction
            interaction = CallInteraction(
                id=str(uuid.uuid4()),
                call_session_id=session_obj.id,
                interaction_type="recording",
                sequence_number=seq,
                recording_sid=recording_sid,
                recording_url=recording_url,
                recording_duration=int(recording_duration) if recording_duration else None,
                s3_audio_url=s3_recording_url,
                transcription_text=whisper_transcript,
                transcription_source="whisper" if whisper_transcript else None,
            )
            db.add(interaction)
            db.commit()
        except Exception as db_exc:
            logger.error(f"DB error saving call interaction: {db_exc}")
            db.rollback()
        finally:
            db.close()
        # --- DB LOGIC END ---
        # --- TEMP FILE LOGIC START ---
        try:
            log_obj = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "call_sid": call_sid,
                "type": "recording",
                "transcript": whisper_transcript,
                "audio_url": s3_recording_url,
                "confidence": None,  # Whisper confidence not available
                "recording_sid": recording_sid,
            }
            with open("/tmp/call_interactions_log.jsonl", "a") as f:
                f.write(json.dumps(log_obj) + "\n")
        except Exception as file_exc:
            logger.error(f"Failed to write call interaction to temp file: {file_exc}")
        # --- TEMP FILE LOGIC END ---
        webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
        recording_webhook = f"{webhook_base_url}/api/calls/handle-recording"
        transcription_webhook = f"{webhook_base_url}/api/calls/handle-transcription"
        response_message = _generate_response_to_user(whisper_transcript)
        audio_url = twilio_service.text_to_speech(response_message)
        if audio_url:
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n    <Play>{audio_url}</Play>\n    <Record \n        action="{recording_webhook}" \n        method="POST" \n        maxLength="60" \n        playBeep="true" \n        timeout="5" \n        transcribe="true" \n        transcribeCallback="{transcription_webhook}"\n        recordingStatusCallback="{recording_webhook}"\n    />\n</Response>"""
        else:
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n    <Say voice="alice">{response_message}</Say>\n    <Record \n        action="{recording_webhook}" \n        method="POST" \n        maxLength="60" \n        playBeep="true" \n        timeout="5" \n        transcribe="true" \n        transcribeCallback="{transcription_webhook}"\n        recordingStatusCallback="{recording_webhook}"\n    />\n</Response>"""
        logger.info(f"Continuing conversation for call {call_sid}")
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        logger.error(f"Error handling recording for call {call_sid}: {e}")
        error_twiml = '''<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n    <Say voice="alice">Sorry, there was an error. Let me try again.</Say>\n    <Record \n        action="/api/calls/handle-recording" \n        method="POST" \n        maxLength="60" \n        playBeep="true" \n        timeout="5" \n        transcribe="true" \n        transcribeCallback="/api/calls/handle-transcription"\n        recordingStatusCallback="/api/calls/handle-recording"\n    />\n</Response>'''
        return Response(content=error_twiml, media_type="application/xml")

@router.post("/handle-transcription")
async def handle_transcription(request: Request):
    """Handle transcription from Twilio (backup to Whisper)."""
    try:
        # Get form data from Twilio
        form_data = await request.form()
        
        transcription_text = form_data.get("TranscriptionText", "")
        transcription_status = form_data.get("TranscriptionStatus", "")
        call_sid = form_data.get("CallSid", "")
        recording_sid = form_data.get("RecordingSid", "")
        
        logger.info(f"Twilio transcription for call {call_sid}: {transcription_text}")
        logger.info(f"Transcription status: {transcription_status}")
        
        # Store transcription in database (you'll need to create a model for this)
        # For now, we'll log it
        logger.info(f"Twilio transcript stored for recording {recording_sid}")
        
        return Response(content="OK", media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Error handling transcription: {e}")
        return Response(content="Error", media_type="text/plain", status_code=500)

def _generate_response_to_user(user_message: str) -> str:
    """Generate a response based on what the user said."""
    if not user_message:
        return "I didn't hear anything. Could you please repeat that?"
    
    user_message = user_message.lower().strip()
    
    # Simple response logic - you can expand this
    if "hello" in user_message or "hi" in user_message:
        return "Hello! How are you doing today?"
    elif "goodbye" in user_message or "bye" in user_message:
        return "Thank you for calling. Have a great day!"
    elif "help" in user_message:
        return "I'm here to help! You can ask me questions or just chat with me."
    elif "repeat" in user_message:
        return "I heard you say: " + user_message
    elif "?" in user_message:
        return "That's an interesting question. Let me think about that."
    else:
        return f"I heard you say: {user_message}. That's interesting! Tell me more."

def _process_speech_input(speech_text: str) -> tuple[str, bool]:
    """Process speech input and return appropriate response and end_call flag."""
    logger.info(f"Processing speech input: '{speech_text}'")
    
    # Simple keyword-based responses
    if "hello" in speech_text or "hi" in speech_text:
        return "Hello! How can I help you today?", False
    
    elif "help" in speech_text:
        return "I can help you with various tasks. Just tell me what you need!", False
    
    elif "weather" in speech_text:
        return "I'm sorry, I don't have access to weather information yet. But I can help you with other tasks!", False
    
    elif "time" in speech_text:
        from datetime import datetime
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}", False
    
    elif "date" in speech_text:
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        return f"Today is {current_date}", False
    
    elif "goodbye" in speech_text or "bye" in speech_text or "end" in speech_text:
        return "Goodbye! Have a great day!", True
    
    elif "thank you" in speech_text or "thanks" in speech_text:
        return "You're welcome! Is there anything else I can help you with?", False
    
    elif "name" in speech_text:
        return "My name is Auto-Caller, your personal assistant!", False
    
    elif "how are you" in speech_text:
        return "I'm doing great, thank you for asking! How are you?", False
    
    elif "joke" in speech_text:
        return "Why don't scientists trust atoms? Because they make up everything!", False
    
    elif "music" in speech_text or "song" in speech_text:
        return "I can't play music yet, but I can help you with other tasks!", False
    
    elif "news" in speech_text:
        return "I don't have access to news yet, but I can help you with other information!", False
    
    elif "reminder" in speech_text or "remind" in speech_text:
        return "I can help you set reminders! Just tell me what you want to be reminded about and when.", False
    
    elif "call" in speech_text:
        return "I can help you make calls! Just provide the phone number and message.", False
    
    else:
        return f"I heard you say '{speech_text}'. I'm still learning, but I can help you with basic tasks like checking the time, setting reminders, or making calls. What would you like to do?", False

@router.get("/recent-interactions")
async def get_recent_interactions():
    """Get recent call sessions with interactions (audio + transcripts) for dashboard."""
    try:
        db = SessionLocal()
        try:
            # Get last 5 call sessions with their interactions
            sessions = db.query(CallSession).order_by(CallSession.created_at.desc()).limit(5).all()
            
            result = []
            for session in sessions:
                # Get interactions for this session
                interactions = db.query(CallInteraction).filter_by(
                    call_session_id=session.id
                ).order_by(CallInteraction.sequence_number).all()
                
                session_data = {
                    "id": session.id,
                    "call_sid": session.call_sid,
                    "from_number": session.from_number,
                    "to_number": session.to_number,
                    "status": session.status,
                    "initial_message": session.initial_message,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "interactions": []
                }
                
                for interaction in interactions:
                    interaction_data = {
                        "id": interaction.id,
                        "type": interaction.interaction_type,
                        "sequence": interaction.sequence_number,
                        "transcript": interaction.transcription_text or interaction.speech_result,
                        "audio_url": interaction.s3_audio_url,
                        "recording_duration": interaction.recording_duration,
                        "confidence": interaction.speech_confidence or interaction.transcription_confidence,
                        "created_at": interaction.created_at.isoformat() if interaction.created_at else None,
                    }
                    session_data["interactions"].append(interaction_data)
                
                result.append(session_data)
            
            return {"success": True, "sessions": result}
            
        except Exception as db_exc:
            logger.error(f"DB error fetching recent interactions: {db_exc}")
            return {"success": False, "error": "Database error"}
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error fetching recent interactions: {e}")
        return {"success": False, "error": str(e)}

@router.get("/recent-interactions-temp")
async def get_recent_interactions_temp():
    """Get last 5 call interactions from the temp log file for dashboard display."""
    log_path = "/tmp/call_interactions_log.jsonl"
    try:
        interactions = []
        with open(log_path, "r") as f:
            lines = f.readlines()
            for line in lines[-5:]:
                try:
                    interactions.append(json.loads(line))
                except Exception:
                    continue
        # Most recent first
        interactions = interactions[::-1]
        return {"success": True, "interactions": interactions}
    except FileNotFoundError:
        return {"success": True, "interactions": []}
    except Exception as e:
        logger.error(f"Error reading temp call interactions log: {e}")
        return {"success": False, "error": str(e)} 