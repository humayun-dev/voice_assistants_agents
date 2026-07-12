"""
Turns text into vectors using Gemini's embedding model.
Uses the SAME GEMINI_API_KEY as the voice assistant -- no second key needed.
"""

import httpx
from app.config.settings import GEMINI_API_KEY
from app.utils.logger import logger

EMBED_MODEL = "gemini-embedding-001"
EMBED_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{EMBED_MODEL}:embedContent"


async def get_embedding(text: str) -> list[float]:
    """Embeds a single piece of text (a document chunk, or a user's
    question) into a vector. Used both at index-build time and at
    query time."""

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{EMBED_URL}?key={GEMINI_API_KEY}",
            json={"content": {"parts": [{"text": text}]}}
        )

        if response.status_code != 200:
            logger.error(f"Embedding request failed: {response.status_code} {response.text}")
            response.raise_for_status()

        data = response.json()
        return data["embedding"]["values"]
