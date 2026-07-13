"""
WhatsApp media download. Incoming voice notes (and images/documents) arrive
in the webhook only as a media_id — the actual bytes have to be fetched in
a separate two-step call:
  1. Ask Graph API for a temporary download URL for this media_id.
  2. Fetch that URL (same access token) to get the raw bytes.
The URL expires quickly, so never cache it — always re-fetch it fresh.
"""
import httpx
from app.config import settings

GRAPH_BASE = "https://graph.facebook.com/v25.0"


async def download_whatsapp_media(media_id: str) -> tuple[bytes, str]:
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
    async with httpx.AsyncClient() as client:
        meta_response = await client.get(f"{GRAPH_BASE}/{media_id}", headers=headers)
        meta_response.raise_for_status()
        media_info = meta_response.json()

        file_response = await client.get(media_info["url"], headers=headers)
        file_response.raise_for_status()
        return file_response.content, media_info["mime_type"]


async def upload_whatsapp_media(file_bytes: bytes, mime_type: str, filename: str) -> str:
    """
    Uploads a file to WhatsApp's servers and returns a media_id — required
    before sending an outbound audio (or image/document) message.
    """
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
    files = {"file": (filename, file_bytes, mime_type)}
    data = {"messaging_product": "whatsapp", "type": mime_type}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GRAPH_BASE}/{settings.WHATSAPP_PHONE_NUMBER_ID}/media",
            headers=headers,
            data=data,
            files=files,
        )
        response.raise_for_status()
        return response.json()["id"]
