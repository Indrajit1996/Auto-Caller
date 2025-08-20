import os
import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
import boto3  # Re-enabled
from botocore.exceptions import ClientError  # Re-enabled
import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import openai
from botocore.exceptions import NoCredentialsError
from twilio.rest import Client
from app.core.config import Config, config

# Load configuration
settings = Config()

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        self.account_sid = config.TWILIO_ACCOUNT_SID
        self.auth_token = config.TWILIO_AUTH_TOKEN
        self.phone_number = config.TWILIO_PHONE_NUMBER
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        # AWS S3 configuration - re-enabled
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-2")
        )
        self.s3_bucket = os.getenv("AWS_S3_BUCKET", "autocaller1323")
        # Initialize OpenAI client for Whisper
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        else:
            logger.warning("OpenAI API key not configured - Whisper transcription will not work")
        # Initialize Twilio client
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            logger.warning("Twilio credentials not found")

    def text_to_speech(self, text: str, voice_id: str = "Zdsf4NBMlHR5zJJ72y9q") -> Optional[str]:
        """Generate MP3 via ElevenLabs and return a public S3 URL."""
        try:
            if not self.elevenlabs_api_key:
                logger.error("ElevenLabs API key not configured")
                return None
            
            # Add pauses to slow down speech
            slowed_text = text.replace(".", "... ").replace(",", ",, ").replace("!", "!... ")
            logger.info(f"Generating TTS for text: {slowed_text[:50]}... with voice_id: {voice_id}")
            eleven_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key,
            }
            payload = {
                "text": slowed_text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                    "speaking_rate": 0.01
                },
                "optimization_level": 0
            }
            logger.info(f"ElevenLabs payload: {payload}")
            logger.info(f"Making request to ElevenLabs: {eleven_url}")
            resp = requests.post(eleven_url, json=payload, headers=headers, timeout=30)
            if resp.status_code != 200:
                logger.error(f"ElevenLabs API error: {resp.status_code} - {resp.text}")
                return None
            audio_bytes = resp.content
            logger.info(f"Received {len(audio_bytes)} bytes from ElevenLabs")
            
            # Upload to S3 and return public URL
            s3_key = f"tts/{uuid.uuid4()}.mp3"
            try:
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=s3_key,
                    Body=audio_bytes,
                    ContentType="audio/mpeg"
                )
                logger.info(f"Uploaded ElevenLabs audio to S3: {s3_key}")
                
                # Return public S3 URL
                s3_url = f"https://{self.s3_bucket}.s3.us-east-2.amazonaws.com/{s3_key}"
                logger.info(f"S3 audio URL: {s3_url}")
                return s3_url
                
            except Exception as e:
                logger.error(f"Failed to upload to S3: {e}")
                return None
        except requests.exceptions.RequestException as exc:
            logger.error(f"ElevenLabs request failed: {exc}")
            return None
        except Exception as exc:
            logger.error(f"ElevenLabs TTS failure: {exc}")
            return None

    def make_call(self, to_number: str, message: str, voice_id: str = "Zdsf4NBMlHR5zJJ72y9q") -> Dict[str, Any]:
        """Make an intelligent conversation call using AI."""
        try:
            if not self.client:
                raise Exception("Twilio client not initialized")
            
            logger.info(f"Making intelligent call to {to_number} with message: {message[:50]}...")
            logger.info(f"Using Twilio phone number: {self.phone_number}")

            # Get webhook URL for intelligent conversation
            webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
            conversation_webhook = f"{webhook_base_url}/api/calls/respond-and-record"

            # Use the intelligent conversation webhook
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather 
        input="speech" 
        timeout="30" 
        speech_timeout="auto" 
        action="{conversation_webhook}?conversation_turn=1" 
        method="POST"
    >
        <Say voice="alice" language="en-US">{message}</Say>
    </Gather>
</Response>'''

            call = self.client.calls.create(
                twiml=twiml,
                to=to_number,
                from_=self.phone_number,
            )
            logger.info(f"Intelligent call initiated. SID: {call.sid}, Status: {call.status}")
            return {
                "success": True,
                "call_sid": call.sid,
                "status": call.status,
                "conversation_webhook": conversation_webhook,
                "to": to_number,
                "from": self.phone_number,
            }
        except TwilioException as exc:
            logger.error(f"Twilio error: {exc}")
            return {"success": False, "error": f"Twilio error: {exc}"}
        except Exception as exc:
            logger.error(f"Call error: {exc}")
            return {"success": False, "error": str(exc)}

    def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """
        Get the status of a call
        """
        try:
            if not self.client:
                raise Exception("Twilio client not initialized")
            
            call = self.client.calls(call_sid).fetch()
            
            return {
                "success": True,
                "call_sid": call.sid,
                "status": call.status,
                "duration": call.duration,
                "start_time": call.start_time,
                "end_time": call.end_time
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error getting call status: {str(e)}")
            return {
                "success": False,
                "error": f"Twilio error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error getting call status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def list_calls(self, limit: int = 20) -> Dict[str, Any]:
        """
        List recent calls
        """
        try:
            if not self.client:
                raise Exception("Twilio client not initialized")
            
            calls = self.client.calls.list(limit=limit)
            
            call_list = []
            for call in calls:
                call_list.append({
                    "sid": call.sid,
                    "status": call.status,
                    "duration": call.duration,
                    "start_time": call.start_time,
                    "end_time": call.end_time,
                    "to": call.to,
                    "from": call.from_
                })
            
            return {
                "success": True,
                "calls": call_list
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error listing calls: {str(e)}")
            return {
                "success": False,
                "error": f"Twilio error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error listing calls: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def transcribe_audio_with_whisper(self, audio_url: str) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper."""
        try:
            if not self.openai_api_key:
                logger.error("OpenAI API key not configured")
                return None
            
            logger.info(f"Transcribing audio with Whisper: {audio_url}")
            
            # For now, skip Whisper transcription since we have Twilio transcription
            logger.info("Skipping Whisper transcription - using Twilio transcription instead")
            return None
                    
        except Exception as exc:
            logger.error(f"Whisper transcription failed: {exc}")
            return None

    def download_and_store_recording(self, recording_url: str, call_sid: str) -> Optional[str]:
        """Download Twilio recording and store in S3."""
        try:
            logger.info(f"Processing recording: {recording_url}")
            
            if not self.client:
                logger.error("Twilio client not initialized")
                return None
                
            # Extract recording SID from URL
            recording_sid = recording_url.split('/')[-1]
            try:
                # Get the recording first
                recording = self.client.recordings(recording_sid).fetch()
                logger.info(f"Found recording: {recording.sid}")
                
                # According to Twilio docs, we need to use the media_content property
                # The recording URL should be accessible directly
                # Twilio provides the recording URL in the recording object
                if hasattr(recording, 'uri'):
                    # Convert the URI to a full URL
                    base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
                    full_recording_url = f"{base_url}/Recordings/{recording_sid}.mp3"
                    logger.info(f"Using Twilio recording URL: {full_recording_url}")
                    return full_recording_url
                else:
                    logger.error("Recording object has no URI attribute")
                    return None
                
            except Exception as twilio_exc:
                logger.error(f"Failed to fetch recording from Twilio: {twilio_exc}")
                return None
            
        except Exception as exc:
            logger.error(f"Failed to process recording: {exc}")
            return None

# Create a global instance
twilio_service = TwilioService()
