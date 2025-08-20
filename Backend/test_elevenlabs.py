import asyncio
import requests
from app.services.elevenlabs_service import ElevenLabsService

async def test():
    service = ElevenLabsService()
    print('API Key:', service.api_key)
    print('Voice ID:', service.voice_id)
    
    # Test with exact same parameters as curl
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{service.voice_id}"
    headers = {
        "xi-api-key": service.api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": "Hello, this is a test.",
        "model_id": "eleven_turbo_v2"
    }
    
    print(f"Testing direct request to: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text[:200]}")
        
        if response.status_code == 200:
            print("Direct request succeeded!")
            audio_bytes = response.content
            print(f"Received {len(audio_bytes)} bytes")
        else:
            print("Direct request failed!")
            
    except Exception as e:
        print(f"Direct request error: {e}")
    
    # Test the service method
    try:
        s3_url, audio_bytes = await service.generate_speech_and_upload("Hello, this is a test.")
        print('Service method result - S3 URL:', s3_url)
    except Exception as e:
        print('Service method error:', e)

if __name__ == "__main__":
    asyncio.run(test()) 