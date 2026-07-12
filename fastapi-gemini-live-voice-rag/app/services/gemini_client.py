# connects to Gemini Live WebSocket
# sends audio chunks
# receives AI responses
# streams back results
# handles RAG tool calls (search_leave_rules) transparently

import asyncio
import json
import websockets
import base64

from app.config.settings import GEMINI_API_KEY, GEMINI_MODEL
from app.config.prompts import load_system_prompt
from app.services import vector_store
from app.utils.logger import logger


# Tool declaration -- Gemini decides on its own, per turn, whether a
# question needs this or can be answered conversationally (AUTO mode,
# which is the default the moment a tool is declared).
SEARCH_TOOL = {
    "function_declarations": [
        {
            "name": "search_leave_rules",
            "description": (
                "Searches the University of Peshawar Leave Rules 1977 for "
                "information about leave policy: types of leave, how much "
                "leave someone is entitled to, eligibility conditions, "
                "durations, or who has the authority to approve it. Use "
                "this whenever the user asks a specific question about "
                "leave rules or policy. Do NOT use this for greetings, "
                "small talk, or general conversation."
            ),
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "query": {
                        "type": "STRING",
                        "description": "The user's question or topic to look up in the leave rules document."
                    }
                },
                "required": ["query"]
            }
        }
    ]
}


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

                "tools": [SEARCH_TOOL],

                "system_instruction": {
                    "parts": [
                        {"text": load_system_prompt()}
                    ]
                }
            }
        }

        await self.ws.send(json.dumps(setup_msg))

        logger.info("Session initialized (with search_leave_rules tool)")

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
    # MANUAL TURN BOUNDARIES
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
    # RAG TOOL CALL HANDLING
    # -------------------------------
    async def _handle_tool_call(self, tool_call: dict):
        """Gemini paused generation and is asking us to run a function.
        We run the retrieval, then send the result straight back on the
        same connection -- the browser never sees this exchange."""

        function_responses = []

        for call in tool_call.get("functionCalls", []):
            call_id = call.get("id")
            name = call.get("name")
            args = call.get("args", {})

            if name == "search_leave_rules":
                query = args.get("query", "")
                logger.info(f"Tool call: search_leave_rules(query={query!r})")
                result_text = await vector_store.search(query, top_k=3)
            else:
                logger.warning(f"Unknown tool call: {name}")
                result_text = f"Unknown tool: {name}"

            function_responses.append({
                "id": call_id,
                "name": name,
                "response": {"result": result_text}
            })

        await self.ws.send(json.dumps({
            "tool_response": {
                "function_responses": function_responses
            }
        }))
        logger.info("Sent tool_response back to Gemini")

    # -------------------------------
    # RECEIVE FROM GEMINI
    # -------------------------------
    async def receive(self):
        if not self.ws:
            return

        async for msg in self.ws:
            try:
                data = json.loads(msg)

                # Intercept tool calls here -- retrieval is an internal
                # round trip with Gemini, not something the browser needs
                # to see. Everything else gets yielded normally.
                if "toolCall" in data:
                    await self._handle_tool_call(data["toolCall"])
                    continue

                yield data

            except Exception as e:
                logger.error(f"Gemini parse error: {e}")

    # -------------------------------
    # CLOSE CONNECTION
    # -------------------------------
    async def close(self):
        if self.ws:
            await self.ws.close()
