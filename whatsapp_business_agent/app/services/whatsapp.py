"""
WhatsApp Cloud API integration. Anything that sends a message outward goes
through here.
"""
import httpx
from app.config import settings


async def send_whatsapp_message(to: str, body: str) -> None:
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(settings.WHATSAPP_API_URL, headers=headers, json=payload)
        print("Send message response:", response.status_code, response.text)


async def send_whatsapp_audio_message(to: str, media_id: str) -> None:
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "audio",
        "audio": {"id": media_id, "voice": True},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(settings.WHATSAPP_API_URL, headers=headers, json=payload)
        print("Send audio response:", response.status_code, response.text)
