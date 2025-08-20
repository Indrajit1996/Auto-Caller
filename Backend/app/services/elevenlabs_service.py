import requests
import boto3
import logging
import os
import json
from app.core.config import config
from typing import Optional, Tuple
import uuid

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = config.ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        self.voice_id = config.ELEVENLABS_VOICE_ID or "Zdsf4NBMlHR5zJJ72y9q"  # Kaymi Malave - Puerto Rican female voice
        
        # AWS S3 setup for audio storage
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION or 'us-east-1'
        )
        self.s3_bucket = config.AWS_S3_BUCKET
        
        if not self.api_key:
            logger.error("ELEVENLABS_API_KEY not found in environment variables")
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
        
        # Ensure S3 bucket is properly configured for public access
        self._ensure_bucket_public_access()
    
    async def generate_speech_and_upload(
        self, 
        text: str, 
        voice_id: str = None,
        file_name: str = None
    ) -> Tuple[Optional[str], Optional[bytes]]:
        """
        Generate high-quality speech from text and upload to S3.
        Returns (s3_url, audio_bytes) tuple.
        """
        try:
            voice = voice_id or self.voice_id
            url = f"{self.base_url}/text-to-speech/{voice}"
            
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "model_id": "eleven_turbo_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            logger.info(f"Making request to ElevenLabs: {url}")
            logger.info(f"ElevenLabs payload: {payload}")
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            audio_bytes = response.content
            logger.info(f"Received {len(audio_bytes)} bytes from ElevenLabs")
            
            # Upload to S3
            s3_url = await self._upload_to_s3(audio_bytes, file_name)
            
            return s3_url, audio_bytes
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return None, None
    
    async def _upload_to_s3(self, audio_bytes: bytes, file_name: str = None) -> Optional[str]:
        """
        Upload audio bytes to S3 and return public URL.
        """
        try:
            if not file_name:
                file_name = f"elevenlabs_audio_{uuid.uuid4()}.mp3"
            
            s3_key = f"audio/elevenlabs/{file_name}"
            
            # Upload to S3 (no ACL needed)
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=audio_bytes,
                ContentType='audio/mpeg'
            )
            
            # Generate presigned URL for secure access
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': s3_key},
                ExpiresIn=3600  # 1 hour expiration
            )
            logger.info(f"Generated presigned URL for ElevenLabs audio: {presigned_url}")
            return presigned_url
            
        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            return None
    
    async def generate_speech_only(self, text: str, voice_id: str = None) -> Optional[bytes]:
        """
        Generate speech without S3 upload (for direct use).
        """
        try:
            voice = voice_id or self.voice_id
            url = f"{self.base_url}/text-to-speech/{voice}"
            
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "model_id": "eleven_turbo_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return None
    
    def _ensure_bucket_public_access(self):
        """
        Ensure S3 bucket is configured for public read access.
        """
        try:
            # Check if bucket exists and is accessible
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
            logger.info(f"S3 bucket {self.s3_bucket} is accessible")
            
            # Try to set bucket policy for public read access
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{self.s3_bucket}/audio/elevenlabs/*"
                    }
                ]
            }
            
            try:
                self.s3_client.put_bucket_policy(
                    Bucket=self.s3_bucket,
                    Policy=json.dumps(bucket_policy)
                )
                logger.info(f"Set public read policy for S3 bucket {self.s3_bucket}")
            except Exception as e:
                logger.warning(f"Could not set bucket policy (this is normal if bucket is already configured): {e}")
                
        except Exception as e:
            logger.error(f"Error configuring S3 bucket: {e}")
    
    def list_voices(self) -> list:
        """
        List available ElevenLabs voices.
        """
        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            voices = response.json().get('voices', [])
            logger.info(f"Found {len(voices)} ElevenLabs voices")
            
            return voices
            
        except Exception as e:
            logger.error(f"Error listing ElevenLabs voices: {e}")
            return [] 