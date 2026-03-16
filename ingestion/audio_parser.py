import tempfile
import os
from openai import OpenAI
from backend.config import GROQ_API_KEY, API_BASE

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=API_BASE
)

def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    """
    Takes audio bytes, saves to a temporary file, and uses Groq's Whisper API
    to transcribe the audio to text.
    """
    ext = os.path.splitext(filename)[1]
    if not ext:
        ext = ".wav"
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name
        
    try:
        with open(temp_audio_path, "rb") as file_to_transcribe:
            transcription = client.audio.transcriptions.create(
                file=file_to_transcribe,
                model="whisper-large-v3",
                response_format="text"
            )
        return transcription
    except Exception as e:
        raise Exception(f"Whisper API Error: {str(e)}")
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
