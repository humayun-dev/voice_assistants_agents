import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.gemini_client import GeminiLiveClient
from app.services.response_parser import GeminiResponseParser
from app.utils.logger import logger

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    logger.info("Client connected")

    gemini = GeminiLiveClient()
    parser = GeminiResponseParser()

    await gemini.connect()

    try:

        # -----------------------------
        # Browser → Gemini (audio stream)
        # -----------------------------
        async def browser_to_gemini():
            while True:
                message = await websocket.receive()

                if "bytes" in message and message["bytes"] is not None:
                    await gemini.send_audio(message["bytes"])

                elif "text" in message and message["text"] is not None:
                    control = message["text"]

                    if control == "activity_start":
                        await gemini.send_activity_start()
                    elif control == "activity_end":
                        await gemini.send_activity_end()
                    else:
                        logger.warning(f"Unknown control message: {control}")

        # -----------------------------
        # Gemini → Browser (parsed stream)
        # -----------------------------
        async def gemini_to_browser():
            async for response in gemini.receive():
                logger.info(f"Raw Gemini message: {response}")

                parsed = parser.parse(response)

                # send structured response to frontend
                await websocket.send_text(
                    f"{parsed['type']}:{parsed['content']}"
                )

        # run both streams concurrently
        await asyncio.gather(
            browser_to_gemini(),
            gemini_to_browser()
        )

    except WebSocketDisconnect:
        logger.info("Client disconnected")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")

    finally:
        await gemini.close()
        logger.info("Gemini connection closed")