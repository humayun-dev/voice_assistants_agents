# connects to Gemini Live WebSocket
# sends audio chunks
# receives AI responses
# streams back results

import asyncio
import json
import websockets
import base64

from app.config.settings import GEMINI_API_KEY, GEMINI_MODEL
from app.config.prompts import load_system_prompt
from app.utils.logger import logger


class GeminiLiveClient:
    def __init__(self):
        self.ws = None

    async def connect(self):

        url = (
            "wss://generativelanguage.googleapis.com/ws/"
            "google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
            f"?key={GEMINI_API_KEY}"
        )

        self.ws = await websockets.connect(url)

        logger.info("Connected to Gemini Live API")

        # -------------------------------
        # 1. SESSION SETUP (IMPORTANT)
        # -------------------------------
        setup_msg = {
            "setup": {
                "model": f"models/{GEMINI_MODEL}",

                "generation_config": {
                    "response_modalities": ["AUDIO"]
                },

                "output_audio_transcription": {},

                "realtime_input_config": {
                    "automatic_activity_detection": {
                        "disabled": True
                    }
                },

                "system_instruction": {
                    "parts": [
                        {"text": load_system_prompt()}
                    ]
                }
            }
        }

        await self.ws.send(json.dumps(setup_msg))

        logger.info("Session initialized")

    # -------------------------------
    # SEND AUDIO TO GEMINI
    # -------------------------------
    async def send_audio(self, audio_bytes: bytes):

        if not self.ws:
            return

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        msg = {
            "realtime_input": {
                "media_chunks": [
                    {
                        "mime_type": "audio/pcm;rate=16000",
                        "data": audio_b64
                    }
                ]
            }
        }

        await self.ws.send(json.dumps(msg))

    # -------------------------------
    # MANUAL TURN BOUNDARIES (automatic VAD is disabled)
    # -------------------------------
    async def send_activity_start(self):
        if not self.ws:
            return
        await self.ws.send(json.dumps({"realtime_input": {"activity_start": {}}}))
        logger.info("Sent activity_start")

    async def send_activity_end(self):
        if not self.ws:
            return
        await self.ws.send(json.dumps({"realtime_input": {"activity_end": {}}}))
        logger.info("Sent activity_end")

    # -------------------------------
    # RECEIVE FROM GEMINI
    # -------------------------------

    async def receive(self):
        if not self.ws:
            return

        async for msg in self.ws:
            try:
                data = json.loads(msg)

                # normalize output format
                yield data

            except Exception as e:
                logger.error(f"Gemini parse error: {e}")

    # -------------------------------
    # CLOSE CONNECTION
    # -------------------------------
    async def close(self):
        if self.ws:
            await self.ws.close()