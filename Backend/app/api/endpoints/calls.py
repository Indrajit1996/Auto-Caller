from datetime import datetime, timezone
import logging
import os
from typing import Optional
import uuid
import json

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
import asyncio
from collections import defaultdict
from pydantic import BaseModel, field_validator
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from app.core.scheduler import scheduler
from app.services.twilio_service import TwilioService
from app.services.elevenlabs_service import ElevenLabsService
from app.services.openai_service import OpenAIService
from app.core.db import SessionLocal
from app.models import CallSession, CallInteraction
import requests

logger = logging.getLogger(__name__)

# Initialize real Twilio service
twilio_service = TwilioService()

router = APIRouter()

# SSE connections storage: call_sid -> list of queues
sse_connections: defaultdict = defaultdict(list)

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
        logger.info(f"DEBUG: make_call endpoint called with to={request.to}, message={request.message[:50]}...")
        
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
            logger.info(f"DEBUG: About to call twilio_service.make_call")
            result = twilio_service.make_call(request.to, request.message, request.voice_id)
            logger.info(f"DEBUG: twilio_service.make_call returned: {result}")
            
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

@router.get("/audio/{recording_sid}")
def proxy_twilio_audio(recording_sid: str):
    """Proxy Twilio recording audio to the client (browser) securely."""
    from app.core.config import config
    account_sid = config.TWILIO_ACCOUNT_SID
    auth_token = config.TWILIO_AUTH_TOKEN
    logger.info(f"Twilio audio proxy using SID: {account_sid}, Token: {auth_token[:4]}...{auth_token[-4:]}")
    twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Recordings/{recording_sid}.mp3"
    resp = requests.get(twilio_url, auth=(account_sid, auth_token), stream=True)
    if resp.status_code != 200:
        logger.error(f"Failed to fetch audio: {resp.status_code} {resp.text}")
        return Response(content=f"Failed to fetch audio: {resp.status_code}", status_code=resp.status_code)
    return StreamingResponse(resp.raw, media_type="audio/mpeg")

@router.get("/audio-file/{filename}")
def serve_audio_file(filename: str):
    """Serve locally stored audio files."""
    import os
    audio_path = f"/tmp/{filename}"
    logger.info(f"Serving audio file: {audio_path}")
    
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    try:
        with open(audio_path, "rb") as f:
            audio_content = f.read()
        logger.info(f"Served audio file: {filename}, size: {len(audio_content)} bytes")
        return Response(content=audio_content, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Error serving audio file {filename}: {e}")
        raise HTTPException(status_code=500, detail="Error serving audio file")

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
    <Say voice="alice" speed="slow">{message}</Say>
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

@router.get("/stream/{call_sid}")
async def stream_call_status(call_sid: str):
    """SSE endpoint to stream call status updates."""
    logger.info(f"Call started   -------------> adsnkjandnjkaj{call_sid}")
    async def event_generator():
        queue = asyncio.Queue()
        sse_connections[call_sid].append(queue)

        try:
            # Send initial connection message
            yield f"data: {json.dumps({'status': 'connected', 'message': 'SSE connected'})}\n\n"

            while True:
                # Wait for status update
                data = await queue.get()

                # Send SSE event
                yield f"data: {json.dumps(data)}\n\n"

                # If call ended, close connection
                if data.get("status") == "completed":
                    break
        except asyncio.CancelledError:
            logger.info(f"SSE connection closed for call {call_sid}")
        finally:
            sse_connections[call_sid].remove(queue)
            if not sse_connections[call_sid]:
                del sse_connections[call_sid]

    logger.info(f"Sending Data to FE --------> {call_sid}")
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

async def broadcast_call_status(call_sid: str, status_data: dict):
    """Broadcast call status to all SSE listeners."""
    logger.info(f"[{call_sid}] Broadcasting status: {status_data} to {len(sse_connections.get(call_sid, []))} listeners")
    if call_sid in sse_connections:
        for queue in sse_connections[call_sid]:
            await queue.put(status_data)
    else:
        logger.warning(f"[{call_sid}] No SSE connections found for this call")

@router.post("/status-callback")
async def call_status_callback(request: Request):
    """Twilio status callback webhook - called when call status changes."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    call_status = form_data.get("CallStatus", "")

    logger.info(f"[{call_sid}] Twilio status callback: {call_status}")

    # Update database
    db = SessionLocal()
    try:
        call_session = db.query(CallSession).filter(CallSession.call_sid == call_sid).first()
        if call_session:
            call_session.status = call_status

            # If call ended, set end time
            if call_status in ["completed", "busy", "no-answer", "failed", "canceled"]:
                call_session.end_time = datetime.now(timezone.utc)

                # Fetch all interactions for this call
                interactions = db.query(CallInteraction).filter(
                    CallInteraction.call_session_id == call_session.id
                ).order_by(CallInteraction.sequence_number).all()

                # Format interactions data
                interactions_data = []
                for interaction in interactions:
                    interactions_data.append({
                        "id": interaction.id,
                        "type": interaction.interaction_type,
                        "sequence": interaction.sequence_number,
                        "transcript": interaction.speech_result,
                        "confidence": interaction.speech_confidence,
                        "system_response": interaction.system_response,
                        "audio_url": interaction.s3_audio_url,  # USER's speech audio (transcript audio)
                        "system_audio_url": interaction.system_audio_url,  # AI's response audio
                        "processing_time": interaction.processing_time
                    })

                # Broadcast call ended with interactions
                await broadcast_call_status(call_sid, {
                    "status": "completed",
                    "message": f"Call {call_status}",
                    "twilio_status": call_status,
                    "interactions": interactions_data,
                    "call_session": {
                        "id": call_session.id,
                        "call_sid": call_session.call_sid,
                        "from_number": call_session.from_number,
                        "to_number": call_session.to_number,
                        "start_time": call_session.start_time.isoformat() if call_session.start_time else None,
                        "end_time": call_session.end_time.isoformat() if call_session.end_time else None,
                        "duration": call_session.duration
                    }
                })

            db.commit()
    except Exception as db_error:
        logger.error(f"[{call_sid}] Database error in status callback: {db_error}")
        db.rollback()
    finally:
        db.close()

    return Response(content="OK", status_code=200)

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


@router.post("/gather-recording-callback")
async def gather_recording_callback(request: Request):
    """Handle recording callback from Gather with recordingEnabled=true."""
    print("="*80)
    print(f"[GATHER-RECORDING-CALLBACK] *** WEBHOOK TRIGGERED ***")
    print("="*80)
    try:
        form_data = await request.form()

        # Log ALL form data to debug
        print(f"[GATHER-RECORDING-CALLBACK] ALL FORM DATA:")
        for key, value in form_data.items():
            print(f"[GATHER-RECORDING-CALLBACK]   {key}: {value}")

        recording_url = form_data.get("RecordingUrl", "")
        recording_sid = form_data.get("RecordingSid", "")
        call_sid = form_data.get("CallSid", "")
        recording_duration = form_data.get("RecordingDuration", "0")

        print(f"[GATHER-RECORDING-CALLBACK] Call {call_sid}: Recording {recording_sid}, duration: {recording_duration}s")
        print(f"[GATHER-RECORDING-CALLBACK] Recording URL: {recording_url}")
        logger.info(f"[{call_sid}] Gather recording callback: {recording_sid}, duration: {recording_duration}s")

        # Check if we have a recording URL
        if not recording_url or not recording_sid:
            print(f"[GATHER-RECORDING-CALLBACK] WARNING: Missing recording URL or SID!")
            print(f"[GATHER-RECORDING-CALLBACK] recording_url: '{recording_url}'")
            print(f"[GATHER-RECORDING-CALLBACK] recording_sid: '{recording_sid}'")
            return Response(content="OK - No recording", status_code=200)

        # Download and store recording in S3 - THIS IS USER SPEECH AUDIO
        print(f"[GATHER-RECORDING-CALLBACK] Starting S3 upload for user speech audio...")
        s3_recording_url = None
        try:
            s3_recording_url = twilio_service.download_and_store_recording(recording_url, call_sid)
            if s3_recording_url:
                print(f"[GATHER-RECORDING-CALLBACK] SUCCESS: User speech stored in S3: {s3_recording_url}")
                logger.info(f"[{call_sid}] Stored user speech recording in S3: {s3_recording_url}")
            else:
                print(f"[GATHER-RECORDING-CALLBACK] ERROR: Failed to get S3 URL for user speech")
                logger.error(f"[{call_sid}] Failed to get S3 URL for user speech recording")
        except Exception as e:
            print(f"[GATHER-RECORDING-CALLBACK] EXCEPTION during S3 upload: {e}")
            logger.warning(f"[{call_sid}] Failed to download user speech recording to S3: {e}")

        # Update the most recent user interaction with the recording URL
        print(f"[GATHER-RECORDING-CALLBACK] Updating database with recording URLs...")
        db = SessionLocal()
        try:
            call_session = db.query(CallSession).filter(CallSession.call_sid == call_sid).first()
            if call_session:
                # Get the most recent speech interaction (user's speech)
                latest_interaction = db.query(CallInteraction).filter(
                    CallInteraction.call_session_id == call_session.id,
                    CallInteraction.interaction_type == "speech",
                    CallInteraction.system_response == None  # User speech has no system_response
                ).order_by(CallInteraction.sequence_number.desc()).first()

                if latest_interaction:
                    latest_interaction.recording_sid = recording_sid
                    latest_interaction.recording_url = recording_url
                    latest_interaction.s3_audio_url = s3_recording_url
                    latest_interaction.recording_duration = int(recording_duration) if recording_duration else None
                    db.commit()
                    print(f"[GATHER-RECORDING-CALLBACK] Database updated - Interaction ID: {latest_interaction.id}")
                    print(f"[GATHER-RECORDING-CALLBACK] - Recording SID: {recording_sid}")
                    print(f"[GATHER-RECORDING-CALLBACK] - S3 URL: {s3_recording_url}")
                    logger.info(f"[{call_sid}] Updated user interaction {latest_interaction.id} with recording URL")
                else:
                    print(f"[GATHER-RECORDING-CALLBACK] WARNING: No user speech interaction found to update")
                    logger.warning(f"[{call_sid}] No user speech interaction found to update with recording")
            else:
                print(f"[GATHER-RECORDING-CALLBACK] WARNING: No call session found for call_sid: {call_sid}")
        except Exception as db_error:
            print(f"[GATHER-RECORDING-CALLBACK] Database error: {db_error}")
            logger.error(f"[{call_sid}] Database error updating user speech recording: {db_error}")
            db.rollback()
        finally:
            db.close()

        return Response(content="OK", status_code=200)

    except Exception as e:
        logger.error(f"Error handling gather recording callback: {e}")
        return Response(content="Error", status_code=500)

@router.post("/handle-recording")
async def handle_recording(request: Request):
    """Handle recording from interactive calls - store audio and continue conversation."""
    try:
        form_data = await request.form()
        recording_url = form_data.get("RecordingUrl", "")
        recording_sid = form_data.get("RecordingSid", "")
        call_sid = form_data.get("CallSid", "")
        recording_duration = form_data.get("RecordingDuration", "0")
        print(f"[HANDLE-RECORDING] Processing recording for call {call_sid}: {recording_sid}, duration: {recording_duration}s")
        logger.info(f"Processing recording for call {call_sid}: {recording_sid}, duration: {recording_duration}s")

        # Check if this is a user audio recording (has RecordingUrl) or system-generated text
        if recording_url and recording_sid:
            # USER AUDIO INPUT - Always store in S3
            print(f"[HANDLE-RECORDING] Detected user audio recording: {recording_sid}")
            twilio_recording_url = recording_url
            whisper_transcript = None

            # MANDATORY: Download and store user recording in S3
            print(f"[HANDLE-RECORDING] Downloading and storing recording in S3...")
            s3_recording_url = twilio_service.download_and_store_recording(recording_url, call_sid)

            if not s3_recording_url:
                print(f"[HANDLE-RECORDING] ERROR: Failed to store user recording in S3 for call {call_sid}")
                logger.error(f"CRITICAL: Failed to store user recording in S3 for call {call_sid}")
            else:
                print(f"[HANDLE-RECORDING] SUCCESS: Stored user recording in S3: {s3_recording_url}")

            # Optional: Try to transcribe with Whisper
            try:
                whisper_transcript = twilio_service.transcribe_audio_with_whisper(recording_url)
                if whisper_transcript:
                    print(f"[HANDLE-RECORDING] Whisper transcription: {whisper_transcript}")
            except Exception as e:
                print(f"[HANDLE-RECORDING] Failed to transcribe with Whisper: {e}")
                logger.warning(f"Failed to transcribe with Whisper: {e}")

            print(f"[HANDLE-RECORDING] Twilio recording URL: {twilio_recording_url}")
            print(f"[HANDLE-RECORDING] S3 recording URL: {s3_recording_url}")
            print(f"[HANDLE-RECORDING] Whisper transcript: {whisper_transcript}")
        else:
            # SYSTEM-GENERATED TEXT - No recording to store
            print(f"[HANDLE-RECORDING] No user recording detected, using system-generated response")
            twilio_recording_url = None
            s3_recording_url = None
            whisper_transcript = None
        
        # --- DB LOGIC START ---
        db = SessionLocal()
        try:
            session_obj = db.query(CallSession).filter_by(call_sid=call_sid).first()
            if not session_obj:
                session_obj = CallSession(
                    id=str(uuid.uuid4()),
                    call_sid=call_sid,
                    twilio_call_sid=call_sid,
                    from_number="",
                    to_number="",
                    status="in_progress",
                )
                db.add(session_obj)
                db.commit()
                db.refresh(session_obj)

            seq = db.query(CallInteraction).filter_by(call_session_id=session_obj.id).count() + 1
            interaction = CallInteraction(
                id=str(uuid.uuid4()),
                call_session_id=session_obj.id,
                interaction_type="recording",
                sequence_number=seq,
                recording_sid=recording_sid,
                recording_url=twilio_recording_url,
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

        webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
        recording_webhook = f"{webhook_base_url}/api/calls/handle-recording"
        transcription_webhook = f"{webhook_base_url}/api/calls/handle-transcription"
        response_message = _generate_response_to_user(whisper_transcript)
        audio_url = twilio_service.text_to_speech(response_message)
        
        twiml_content = ""
        if audio_url:
            twiml_content = f"""<Response>
    <Play>{audio_url}</Play>
    <Record action="{recording_webhook}" method="POST" maxLength="60" playBeep="true" timeout="5" transcribe="true" transcribeCallback="{transcription_webhook}" recordingStatusCallback="{recording_webhook}"/>
</Response>"""
        else:
            twiml_content = f"""<Response>
    <Say voice="alice" speed="slow">{response_message}</Say>
    <Record action="{recording_webhook}" method="POST" maxLength="60" playBeep="true" timeout="5" transcribe="true" transcribeCallback="{transcription_webhook}" recordingStatusCallback="{recording_webhook}"/>
</Response>"""
        
        logger.info(f"Continuing conversation for call {call_sid}")
        return Response(content=f'<?xml version="1.0" encoding="UTF-8"?>{twiml_content}', media_type="application/xml")

    except Exception as e:
        logger.error(f"Error handling recording for call {call_sid}: {e}")
        error_twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" speed="slow">Sorry, there was an error. Let me try again.</Say>
    <Record action="/api/calls/handle-recording" method="POST" maxLength="60" playBeep="true" timeout="5" transcribe="true" transcribeCallback="/api/calls/handle-transcription" recordingStatusCallback="/api/calls/handle-recording"/>
</Response>'''
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
        
        # Save transcription to database
        db = SessionLocal()
        try:
            # Find the CallInteraction with this recording_sid
            interaction = db.query(CallInteraction).filter_by(recording_sid=recording_sid).first()
            if interaction:
                interaction.transcription_text = transcription_text
                interaction.transcription_status = transcription_status
                db.commit()
                logger.info(f"Transcription saved to database for recording {recording_sid}")
            else:
                logger.warning(f"No CallInteraction found for recording_sid: {recording_sid}")
        except Exception as db_exc:
            logger.error(f"DB error saving transcription: {db_exc}")
            db.rollback()
        finally:
            db.close()
        
        return Response(content="OK", media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Error handling transcription: {e}")
        return Response(content="Error", media_type="text/plain", status_code=500)

def _generate_elevenlabs_audio(text: str, call_sid: str) -> str:
    """Generate ElevenLabs audio and return the local URL."""
    logger.info(f"[{call_sid}] DEBUG: _generate_elevenlabs_audio called with text: {text[:50]}...")
    try:
        twilio_service = TwilioService()
        logger.info(f"[{call_sid}] TwilioService initialized")
        audio_url = twilio_service.text_to_speech(text)
        logger.info(f"[{call_sid}] Generated ElevenLabs audio: {audio_url}")
        return audio_url
    except Exception as e:
        logger.error(f"[{call_sid}] EXCEPTION in _generate_elevenlabs_audio: {e}")
        logger.error(f"[{call_sid}] ElevenLabs error: {e}")
        return None

@router.post("/respond-and-record")
async def respond_and_record(request: Request):
    """Webhook endpoint for intelligent conversation with AI."""
    import time
    start_time = time.monotonic()
    logger.info(f"=== CONVERSATION START: {start_time} ===")
    print('User responded ------------------->', request)
    try:
        # Get form data from Twilio
        form_data = await request.form()

        # Log ALL form data for debugging
        print(f"[RESPOND-AND-RECORD] === ALL FORM DATA ===")
        for key, value in form_data.items():
            print(f"[RESPOND-AND-RECORD] {key}: {value}")
        print(f"[RESPOND-AND-RECORD] === END FORM DATA ===")

        # Extract parameters
        call_sid = form_data.get("CallSid", "")
        speech_text = form_data.get("SpeechResult", "")
        confidence = form_data.get("Confidence", "0")
        recording_url = form_data.get("RecordingUrl", "")
        recording_sid = form_data.get("RecordingSid", "")

        print(f"[RESPOND-AND-RECORD] CallSid: {call_sid}")
        print(f"[RESPOND-AND-RECORD] SpeechResult: {speech_text}")
        print(f"[RESPOND-AND-RECORD] RecordingUrl: {recording_url}")
        print(f"[RESPOND-AND-RECORD] RecordingSid: {recording_sid}")

        logger.info(f"[{call_sid}] User said: '{speech_text}' (confidence: {confidence}) - elapsed: {time.monotonic() - start_time:.2f}s")

        # Get or create call session
        db = SessionLocal()
        call_session_id = None
        user_interaction_id = None
        try:
            # Get or create call session
            call_session = db.query(CallSession).filter(CallSession.call_sid == call_sid).first()
            if not call_session:
                call_session = CallSession(
                    id=str(uuid.uuid4()),
                    call_sid=call_sid,
                    from_number=form_data.get("From", ""),
                    to_number=form_data.get("To", ""),
                    status="in-progress"
                )
                db.add(call_session)
                db.commit()
                db.refresh(call_session)

                # Broadcast call started
                await broadcast_call_status(call_sid, {
                    "status": "in-progress",
                    "message": "Call in progress"
                })

            # Store call_session_id before closing the session
            call_session_id = call_session.id

            # Get next sequence number
            max_sequence = db.query(CallInteraction).filter(
                CallInteraction.call_session_id == call_session_id
            ).count()

            # Create interaction with user's speech (will add AI response later)
            if speech_text:
                user_interaction = CallInteraction(
                    id=str(uuid.uuid4()),
                    call_session_id=call_session_id,
                    interaction_type="speech",
                    sequence_number=max_sequence + 1,
                    speech_result=speech_text,
                    speech_confidence=float(confidence) if confidence else None
                )
                db.add(user_interaction)
                db.commit()
                db.refresh(user_interaction)
                user_interaction_id = user_interaction.id

                if recording_url and recording_sid:
                    print(f"[RESPOND-AND-RECORD] Found recording in webhook payload: {recording_sid}")
                    try:
                        s3_audio_url = twilio_service.download_and_store_recording(recording_url, call_sid)
                        if s3_audio_url:
                            print(f"[RESPOND-AND-RECORD] SUCCESS: Stored recording in S3: {s3_audio_url}")
                            user_interaction.s3_audio_url = s3_audio_url
                            user_interaction.recording_sid = recording_sid
                            user_interaction.recording_url = recording_url
                            db.commit()
                        else:
                            print(f"[RESPOND-AND-RECORD] ERROR: Failed to download recording from webhook URL")
                    except Exception as rec_error:
                        print(f"[RESPOND-AND-RECORD] EXCEPTION storing webhook recording: {rec_error}")
                        import traceback
                        traceback.print_exc()
                else:
                    # Fall back to fetching from Twilio REST API if the gather webhook did not include recording data yet
                    print(f"[RESPOND-AND-RECORD] No recording URL in form data - fetching from Twilio API...")
                    try:
                        import time
                        time.sleep(1)  # Wait 1 second for Twilio to process the recording

                        # Fetch recordings for this call from Twilio
                        from app.services.twilio_service import twilio_service as tw_service
                        recordings = tw_service.client.recordings.list(call_sid=call_sid, limit=1)
                        print(f"[RESPOND-AND-RECORD] recording url value  {call_sid}")
                        print(f"[RESPOND-AND-RECORD] recording url value  {recordings}")
                        if recordings:
                            latest_recording = recordings[0]
                            recording_sid = latest_recording.sid
                            recording_url = f"https://api.twilio.com{latest_recording.uri.replace('.json', '')}"

                            print(f"[RESPOND-AND-RECORD] Found recording: {recording_sid}")
                            print(f"[RESPOND-AND-RECORD] Recording URL: {recording_url}")

                            # Download and store in S3
                            s3_audio_url = twilio_service.download_and_store_recording(recording_url, call_sid)
                            if s3_audio_url:
                                print(f"[RESPOND-AND-RECORD] SUCCESS: Stored recording in S3: {s3_audio_url}")
                                user_interaction.s3_audio_url = s3_audio_url
                                user_interaction.recording_sid = recording_sid
                                user_interaction.recording_url = recording_url
                                db.commit()
                            else:
                                print(f"[RESPOND-AND-RECORD] ERROR: Failed to download recording")
                        else:
                            print(f"[RESPOND-AND-RECORD] No recordings found for this call yet")
                    except Exception as rec_error:
                        print(f"[RESPOND-AND-RECORD] EXCEPTION fetching recording: {rec_error}")
                        import traceback
                        traceback.print_exc()
        except Exception as db_error:
            logger.error(f"[{call_sid}] Database error storing user speech: {db_error}")
            db.rollback()
        finally:
            db.close()

        # Check for goodbye keywords only
        goodbye_keywords = ["goodbye", "bye", "good bye", "see you", "talk to you later", "end call", "hang up"]
        is_goodbye = any(keyword.lower() in speech_text.lower() for keyword in goodbye_keywords)
        
        if is_goodbye:
            # Generate a proper goodbye response
            if speech_text:
                try:
                    openai_service = OpenAIService()
                    message = await openai_service.generate_final_response(speech_text)
                except Exception as e:
                    logger.error(f"Error generating final response: {e}")
                    message = "Thank you for talking with me. Take care and have a wonderful day!"
            else:
                message = "Thank you for talking with me. Take care and have a wonderful day!"

            # Update call status to completed
            db = SessionLocal()
            try:
                call_session = db.query(CallSession).filter(CallSession.call_sid == call_sid).first()
                if call_session:
                    call_session.status = "completed"
                    call_session.end_time = datetime.now(timezone.utc)
                    db.commit()

                    # Broadcast call ended
                    await broadcast_call_status(call_sid, {
                        "status": "completed",
                        "message": "Call ended"
                    })
            except Exception as db_error:
                logger.error(f"[{call_sid}] Database error updating call status: {db_error}")
                db.rollback()
            finally:
                db.close()
        else:
            # Generate normal conversation response
            openai_start = time.monotonic()
            logger.info(f"[{call_sid}] Starting OpenAI API call - elapsed: {openai_start - start_time:.2f}s")
            try:
                openai_service = OpenAIService()
                message = await openai_service.generate_conversation_response(
                    conversation_history=[],
                    user_input=speech_text if speech_text else "Hello"
                )
                openai_end = time.monotonic()
                logger.info(f"[{call_sid}] OpenAI API call completed in {openai_end - openai_start:.2f}s - total elapsed: {openai_end - start_time:.2f}s")
                if not message:
                    message = "I'm here to check in on you. How are you doing today?"
            except Exception as e:
                openai_end = time.monotonic()
                logger.error(f"OpenAI error after {openai_end - start_time:.2f}s: {e}")
                message = "I'm here to check in on you. How are you doing today?"
        
        # Generate ElevenLabs audio
        audio_start = time.monotonic()
        logger.info(f"[{call_sid}] Starting ElevenLabs audio generation - elapsed: {audio_start - start_time:.2f}s")
        audio_url = None
        try:
            audio_url = _generate_elevenlabs_audio(message, call_sid)
            audio_end = time.monotonic()
            logger.info(f"[{call_sid}] ElevenLabs audio generation completed in {audio_end - audio_start:.2f}s - total elapsed: {audio_end - start_time:.2f}s")
        except Exception as e:
            audio_end = time.monotonic()
            logger.error(f"[{call_sid}] Failed to generate ElevenLabs audio after {audio_end - start_time:.2f}s: {e}")
        
        # Create TwiML response
        twiml_start = time.monotonic()
        logger.info(f"[{call_sid}] Starting TwiML generation - elapsed: {twiml_start - start_time:.2f}s")
        from twilio.twiml.voice_response import VoiceResponse
        twiml = VoiceResponse()
        
        if audio_url:
            # Play ElevenLabs audio
            twiml.play(audio_url)
        else:
            # Fallback to Twilio TTS
            twiml.say(message, voice="alice", language="en-US")
        
        # Set up recording and listening for next response
        webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
        conversation_webhook = f"{webhook_base_url}/api/calls/respond-and-record"
        recording_status_callback = f"{webhook_base_url}/api/calls/gather-recording-callback"

        # Smart speech recognition with auto timeout and recording enabled
        gather = twiml.gather(
            input="speech",
            timeout=3,
            speech_timeout="auto",
            action=conversation_webhook,
            method="POST",
            speech_model="phone_call",
            record=True,
            recording_status_callback=recording_status_callback,
            recording_status_callback_method="POST"
        )
        
        # Try to generate ElevenLabs audio for "I am listening"
        listening_start = time.monotonic()
        logger.info(f"[{call_sid}] Starting 'I am listening' audio generation - elapsed: {listening_start - start_time:.2f}s")
        try:
            listening_audio = _generate_elevenlabs_audio("I am listening", call_sid)
            listening_end = time.monotonic()
            logger.info(f"[{call_sid}] 'I am listening' audio generation completed in {listening_end - listening_start:.2f}s - total elapsed: {listening_end - start_time:.2f}s")
            if listening_audio:
                gather.play(listening_audio)
            else:
                gather.say("I am listening", voice="alice", language="en-US")
        except Exception as e:
            listening_end = time.monotonic()
            logger.error(f"[{call_sid}] Failed to generate ElevenLabs audio for 'I am listening' after {listening_end - start_time:.2f}s: {e}")
            gather.say("I am listening", voice="alice", language="en-US")
        
        # Update the same interaction with AI response
        db = SessionLocal()
        try:
            if user_interaction_id:
                # Update the existing user interaction with AI response
                user_interaction = db.query(CallInteraction).filter(
                    CallInteraction.id == user_interaction_id
                ).first()
                if user_interaction:
                    user_interaction.system_response = message
                    user_interaction.system_audio_url = audio_url
                    user_interaction.processing_time = time.monotonic() - start_time
                    db.commit()
                    logger.info(f"[{call_sid}] Updated interaction {user_interaction_id} with AI response")
            else:
                # If no user interaction was created (e.g., empty speech), create a new one with AI response only
                call_session = db.query(CallSession).filter(CallSession.call_sid == call_sid).first()
                if call_session:
                    max_sequence = db.query(CallInteraction).filter(
                        CallInteraction.call_session_id == call_session.id
                    ).count()

                    ai_interaction = CallInteraction(
                        id=str(uuid.uuid4()),
                        call_session_id=call_session.id,
                        interaction_type="speech",
                        sequence_number=max_sequence + 1,
                        system_response=message,
                        system_audio_url=audio_url,
                        processing_time=time.monotonic() - start_time
                    )
                    db.add(ai_interaction)
                    db.commit()
                    logger.info(f"[{call_sid}] Created new interaction with AI response only")
        except Exception as db_error:
            logger.error(f"[{call_sid}] Database error storing AI response: {db_error}")
            db.rollback()
        finally:
            db.close()

        twiml_end = time.monotonic()
        logger.info(f"[{call_sid}] TwiML generation completed in {twiml_end - twiml_start:.2f}s - total elapsed: {twiml_end - start_time:.2f}s")
        logger.info(f"[{call_sid}] CONVERSATION COMPLETE - Total time: {twiml_end - start_time:.2f}s")
        return Response(content=str(twiml), media_type="application/xml")
        
    except Exception as e:
        end_time = time.monotonic()
        logger.error(f"Error in respond_and_record after {end_time - start_time:.2f}s: {e}")
        # Return a simple response in case of error
        from twilio.twiml.voice_response import VoiceResponse
        twiml = VoiceResponse()
        twiml.say("I'm sorry, there was an error. Please try again.", voice="alice", language="en-US")
        return Response(content=str(twiml), media_type="application/xml")

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
        logger.info(f"Here --------------->")
        # logger.info(f"Interactions {interactions}")
        try:
            # Get last 50 call sessions with their interactions
            sessions = db.query(CallSession).order_by(CallSession.created_at.desc()).limit(50).all()
            
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
                        "system_response": interaction.system_response,
                        "audio_url": interaction.s3_audio_url,  # USER's speech audio (transcript audio)
                        "system_audio_url": interaction.system_audio_url,  # AI's response audio
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