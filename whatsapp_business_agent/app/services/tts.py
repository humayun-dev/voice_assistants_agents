"""
Text-to-speech via Gemini. Returns raw PCM audio (16-bit signed, mono,
24kHz) — the native format Gemini's TTS API returns. This is NOT a file
WhatsApp can send directly; it needs converting to OGG/Opus first
(see audio_convert.py).
"""
from google import genai
from google.genai import types
from app.config import settings

_genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

TTS_MODEL = "gemini-2.5-flash-preview-tts"
VOICE_NAME = "Kore"
PCM_SAMPLE_RATE = 24000


def synthesize_speech(text: str) -> bytes:
    response = _genai_client.models.generate_content(
        model=TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE_NAME)
                )
            ),
        ),
    )
    return response.candidates[0].content.parts[0].inline_data.data
