"""
Audio transcription via Gemini. Uses the raw google-genai SDK directly
(rather than langchain) since this is a one-off multimodal call, not part
of the conversational agent graph.
"""
import json
from google import genai
from google.genai import types
from app.config import settings

_genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

TRANSCRIPTION_INSTRUCTION = (
    "Transcribe this voice message exactly as spoken. Also identify the "
    "spoken language. Respond with ONLY valid JSON, no other text, in this "
    "exact shape:\n"
    '{"transcript": "...", "language": "english" | "urdu" | "pashto" | "other"}'
)


def transcribe_audio(audio_bytes: bytes, mime_type: str) -> dict:
    """
    Returns {"transcript": str, "language": "english"|"urdu"|"pashto"|"other"}.
    Falls back to language="other" if the model doesn't return valid JSON,
    so a parsing hiccup never crashes the webhook — it just means the reply
    goes out as text instead of voice.
    """
    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
    response = _genai_client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[audio_part, TRANSCRIPTION_INSTRUCTION],
    )
    raw = response.text.strip().removeprefix("```json").removesuffix("```").strip()

    try:
        parsed = json.loads(raw)
        return {
            "transcript": parsed.get("transcript", "").strip(),
            "language": parsed.get("language", "other").strip().lower(),
        }
    except (json.JSONDecodeError, AttributeError):
        print(f"[Transcription] Could not parse language JSON, falling back to raw text: {raw}")
        return {"transcript": raw, "language": "other"}
