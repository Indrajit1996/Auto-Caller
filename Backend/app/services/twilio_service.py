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
from app.services.elevenlabs_service import ElevenLabsService

# Load configuration
settings = Config()

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        self.account_sid = config.TWILIO_ACCOUNT_SID
        self.auth_token = config.TWILIO_AUTH_TOKEN
        self.phone_number = config.TWILIO_PHONE_NUMBER
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Initialize ElevenLabs service for TTS with S3 storage
        try:
            self.elevenlabs_service = ElevenLabsService()
            logger.info("ElevenLabsService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ElevenLabsService: {e}")
            self.elevenlabs_service = None

        # AWS S3 configuration - re-enabled for recordings
        aws_region = os.getenv("AWS_REGION", "us-east-2")
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=aws_region,
            config=boto3.session.Config(signature_version='s3v4', region_name=aws_region)
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
        """Generate MP3 via ElevenLabs, upload to S3, and return presigned URL."""
        print(f"[TTS] Starting text_to_speech function")
        print(f"[TTS] Input text: {text}")
        print(f"[TTS] Input text length: {len(text)}")
        print(f"[TTS] Voice ID: {voice_id}")

        try:
            print(f"[TTS] Checking if ElevenLabsService is initialized...")
            if not self.elevenlabs_service:
                print(f"[TTS] ERROR: ElevenLabsService not initialized!")
                logger.error("ElevenLabsService not initialized")
                return None

            print(f"[TTS] ElevenLabsService is initialized, proceeding with TTS generation")
            logger.info(f"Generating TTS for text: {text[:50]}... with voice_id: {voice_id}")

            # Generate speech and upload to S3
            print(f"[TTS] Calling elevenlabs_service.generate_speech_and_upload...")
            print(f"[TTS] Parameters - text length: {len(text)}, voice_id: {voice_id}")

            s3_url, audio_bytes = self.elevenlabs_service.generate_speech_and_upload(
                text=text,
                voice_id=voice_id,
                file_name=f"{uuid.uuid4()}.mp3"
            )

            print(f"[TTS] generate_speech_and_upload completed")
            print(f"[TTS] S3 URL returned: {s3_url}")
            print(f"[TTS] Audio bytes length: {len(audio_bytes) if audio_bytes else 'None'}")

            if s3_url:
                print(f"[TTS] SUCCESS: Audio generated and uploaded to S3")
                print(f"[TTS] Full S3 URL: {s3_url}")
                logger.info(f"Successfully generated and uploaded audio to S3. Presigned URL: {s3_url[:100]}...")
                return s3_url
            else:
                print(f"[TTS] ERROR: Failed to generate speech or upload to S3")
                logger.error("Failed to generate speech or upload to S3")
                return None

        except Exception as exc:
            print(f"[TTS] EXCEPTION occurred in text_to_speech: {exc}")
            print(f"[TTS] Exception type: {type(exc).__name__}")
            import traceback
            print(f"[TTS] Full traceback:")
            traceback.print_exc()
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
            status_callback_url = f"{webhook_base_url}/api/calls/status-callback"
            logger.info(f"Using webhook URL: {conversation_webhook}")
            logger.info(f"Using status callback URL: {status_callback_url}")

            # Generate ElevenLabs audio for the initial message
            initial_audio_url = self.text_to_speech(message, voice_id)
            
            # Use the intelligent conversation webhook
            recording_status_callback = f"{webhook_base_url}/api/calls/gather-recording-callback"
            print(f'[TWILIO] recording_status_callback: {recording_status_callback}')
            if initial_audio_url:
                # Use ElevenLabs audio
                twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather
        input="speech"
        timeout="3"
        speech_timeout="auto"
        action="{conversation_webhook}"
        method="POST"
        speech_model="phone_call"
        recordingEnabled="true"
        recordingStatusCallback="{recording_status_callback}"
        recordingStatusCallbackMethod="POST"
    >
        <Play>{initial_audio_url}</Play>
    </Gather>
</Response>'''
            else:
                # Fallback to Twilio TTS
                twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather
        input="speech"
        timeout="3"
        speech_timeout="auto"
        action="{conversation_webhook}"
        method="POST"
        speech_model="phone_call"
        recordingEnabled="true"
        recordingStatusCallback="{recording_status_callback}"
        recordingStatusCallbackMethod="POST"
    >
        <Say voice="alice" language="en-US">{message}</Say>
    </Gather>
</Response>'''
            
            logger.info(f"Generated TwiML: {twiml}")

            call = self.client.calls.create(
                twiml=twiml,
                to=to_number,
                from_=self.phone_number,
                status_callback=status_callback_url,
                status_callback_event=["initiated", "ringing", "answered", "completed"],
                status_callback_method="POST"
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
        """Download Twilio recording and store in S3, return presigned URL."""
        print(f"[USER-RECORDING] Starting download_and_store_recording")
        print(f"[USER-RECORDING] Recording URL from Twilio: {recording_url}")
        print(f"[USER-RECORDING] Call SID: {call_sid}")

        try:
            logger.info(f"Processing recording: {recording_url}")

            if not self.client:
                print(f"[USER-RECORDING] ERROR: Twilio client not initialized")
                logger.error("Twilio client not initialized")
                return None

            # Extract recording SID from URL
            recording_sid = recording_url.split('/')[-1]
            print(f"[USER-RECORDING] Extracted recording SID: {recording_sid}")

            try:
                # Get the recording first
                print(f"[USER-RECORDING] Fetching recording from Twilio API...")
                recording = self.client.recordings(recording_sid).fetch()
                print(f"[USER-RECORDING] Found recording: {recording.sid}")
                logger.info(f"Found recording: {recording.sid}")

                # Download the recording from Twilio
                base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
                full_recording_url = f"{base_url}/Recordings/{recording_sid}.mp3"
                print(f"[USER-RECORDING] Downloading from: {full_recording_url}")

                # Download the recording
                auth = (self.account_sid, self.auth_token)
                response = requests.get(full_recording_url, auth=auth, timeout=30)

                if response.status_code != 200:
                    print(f"[USER-RECORDING] ERROR: Failed to download recording - HTTP {response.status_code}")
                    logger.error(f"Failed to download recording: {response.status_code}")
                    return None

                audio_bytes = response.content
                print(f"[USER-RECORDING] Downloaded {len(audio_bytes)} bytes from Twilio")
                logger.info(f"Downloaded {len(audio_bytes)} bytes from Twilio")

                # Upload to S3
                s3_key = f"audio/recordings/{call_sid}/{recording_sid}.mp3"
                print(f"[USER-RECORDING] Uploading to S3 with key: {s3_key}")

                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=s3_key,
                    Body=audio_bytes,
                    ContentType='audio/mpeg'
                )
                print(f"[USER-RECORDING] Successfully uploaded to S3 bucket: {self.s3_bucket}")

                # Generate presigned URL (consistent with ElevenLabs audio)
                aws_region = os.getenv("AWS_REGION", "us-east-2")
                print(f"[USER-RECORDING] Generating presigned URL (expires in 1 hour)...")

                try:
                    presigned_url = self.s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': self.s3_bucket,
                            'Key': s3_key
                        },
                        ExpiresIn=3600  # 1 hour
                    )
                    print(f"[USER-RECORDING] SUCCESS: Generated presigned URL")
                    print(f"[USER-RECORDING] Presigned URL: {presigned_url}")
                    logger.info(f"Uploaded recording to S3: {s3_key}")
                    logger.info(f"Generated presigned URL: {presigned_url}")
                    return presigned_url
                except Exception as presign_exc:
                    print(f"[USER-RECORDING] WARNING: Failed to generate presigned URL: {presign_exc}")
                    print(f"[USER-RECORDING] Falling back to public URL...")
                    # Fallback to public URL if presigned fails
                    public_url = f"https://{self.s3_bucket}.s3.{aws_region}.amazonaws.com/{s3_key}"
                    print(f"[USER-RECORDING] Public URL: {public_url}")
                    logger.warning(f"Failed to generate presigned URL, using public URL: {public_url}")
                    return public_url

            except Exception as twilio_exc:
                print(f"[USER-RECORDING] ERROR: Failed to fetch recording from Twilio: {twilio_exc}")
                logger.error(f"Failed to fetch recording from Twilio: {twilio_exc}")
                return None

        except Exception as exc:
            print(f"[USER-RECORDING] EXCEPTION: {exc}")
            import traceback
            print(f"[USER-RECORDING] Full traceback:")
            traceback.print_exc()
            logger.error(f"Failed to process recording: {exc}")
            return None

# Create a global instance
twilio_service = TwilioService()
