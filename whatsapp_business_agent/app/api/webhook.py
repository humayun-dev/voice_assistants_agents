from fastapi import APIRouter, Request, Response
from langchain_core.messages import HumanMessage

from app.config import settings
from app.agents.graph import graph
from app.agents.utils import extract_text
from app.services.whatsapp import send_whatsapp_message, send_whatsapp_audio_message
from app.services.media import download_whatsapp_media, upload_whatsapp_media
from app.services.transcription import transcribe_audio
from app.services.tts import synthesize_speech
from app.services.audio_convert import pcm_to_ogg_opus

router = APIRouter()

# Voice replies are only sent back for these languages for now — Pashto TTS
# quality hasn't been verified yet, so Pashto voice notes get a text reply.
VOICE_REPLY_LANGUAGES = {"english", "urdu", "pashto"}


@router.get("/webhook")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WEBHOOK_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Verification failed", status_code=403)


async def extract_incoming_message(message: dict) -> tuple[str, bool, str] | None:
    """
    Returns (text, was_voice, language) for the agent graph, regardless of
    whether the customer typed or spoke it. Returns None for unsupported
    message types so the caller can skip them gracefully.
    """
    message_type = message.get("type")

    if message_type == "text":
        return message["text"]["body"], False, "unknown"

    if message_type == "audio":
        media_id = message["audio"]["id"]
        audio_bytes, mime_type = await download_whatsapp_media(media_id)
        result = transcribe_audio(audio_bytes, mime_type)
        print(f"[Transcription] ({result['language']}) {result['transcript']}")
        return result["transcript"], True, result["language"]

    print(f"Unsupported message type: {message_type} — ignoring.")
    return None


async def reply_to_customer(sender: str, reply_text: str, should_reply_with_voice: bool) -> None:
    if not should_reply_with_voice:
        await send_whatsapp_message(sender, reply_text)
        return

    try:
        pcm_audio = synthesize_speech(reply_text)
        ogg_audio = pcm_to_ogg_opus(pcm_audio)
        media_id = await upload_whatsapp_media(ogg_audio, "audio/ogg", "reply.ogg")
        await send_whatsapp_audio_message(sender, media_id)
    except Exception as e:
        # If voice synthesis/upload fails for any reason, don't let the
        # customer get no reply at all — fall back to text.
        print(f"[Voice reply] Failed to generate/send voice reply, falling back to text: {e}")
        await send_whatsapp_message(sender, reply_text)


@router.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()
    try:
        value = body["entry"][0]["changes"][0]["value"]
        if "messages" in value:
            message = value["messages"][0]
            sender = message["from"]

            extracted = await extract_incoming_message(message)
            if extracted is None:
                return Response(status_code=200)
            text, was_voice, language = extracted

            print(f"Message from {sender}: {text}")

            config = {"configurable": {"thread_id": sender}}
            result = graph.invoke({"messages": [HumanMessage(content=text)]}, config=config)
            reply_text = extract_text(result["messages"][-1])

            print(f"Reply ({result['intent']}): {reply_text}")

            should_reply_with_voice = was_voice and language in VOICE_REPLY_LANGUAGES
            await reply_to_customer(sender, reply_text, should_reply_with_voice)
        else:
            print("Non-message event (status update) — ignoring.")
    except (KeyError, IndexError) as e:
        print("Malformed payload:", e)

    return Response(status_code=200)
