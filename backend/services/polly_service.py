
import boto3
import os
import base64
from botocore.exceptions import BotoCoreError, ClientError
import logging

logger = logging.getLogger(__name__)

# Initialize Polly client
APP_REGION = os.getenv("AWS_REGION", "us-west-2")
polly_client = boto3.client('polly', region_name=APP_REGION)

# Normalize language names to mapped keys
VOICE_MAPPING = {
    "english": "Joanna",
    "hindi": "Aditi",
    "hinglish": "Aditi", # Handle Hinglish explicitly
    "हिंदी": "Aditi", # Handle Devanagari script for Hindi
    "marathi": "Aditi", # Fallback to Aditi for Marathi (Devanagari)
    "mr": "Aditi",
    "मराठी": "Aditi", # Marathi in Devanagari
    "spanish": "Mia",
    "french": "Celine",
}

def generate_audio_base64(text, language="English"):
    """
    Generates speech from text using AWS Polly and returns it as a base64 encoded string.
    """
    try:
        # Accept various language forms: 'Marathi', 'mr', 'मराठी', 'marathi'
        lang_key = (language or '').strip().lower()
        if lang_key == 'marathi' or lang_key == 'mr':
            lang_key = 'marathi'

        # Default to Joanna (English) if language not found
        voice_id = VOICE_MAPPING.get(lang_key, 'Joanna')

        try:
            response = polly_client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                Engine='neural'
            )
        except (BotoCoreError, ClientError) as e:
            logger.warning(f"Neural engine failed for voice {voice_id}, falling back to standard. Error: {e}")
            response = polly_client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                Engine='standard'
            )

        audio_stream = response.get('AudioStream')
        if audio_stream:
            audio_bytes = audio_stream.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            return audio_base64

        return None

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Polly error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in TTS: {e}")
        return None
