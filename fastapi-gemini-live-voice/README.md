# Gemini Live Voice Assistant

A real-time, voice-to-voice assistant built on **FastAPI** and **Google's Gemini Live API**. Talk to it naturally through your browser — it listens, responds out loud, and supports interrupting it mid-sentence like a real conversation, with no button presses needed between turns.

## Features

- **Real-time voice conversation** over a persistent WebSocket connection to Gemini's Live API (`BidiGenerateContent`), not request/response HTTP.
- **Client-side voice activity detection (VAD)** — the browser decides exactly when the user starts and stops talking (local RMS volume + hysteresis), and drives Gemini's turn boundaries explicitly rather than relying on server-side automatic detection. This avoids the duplicate/phantom replies that automatic detection can produce.
- **Barge-in / interruption support** — talking over the assistant while it's speaking cuts it off immediately and hands control back to the user right away.
- **Clean separation of concerns** — the backend is a pure relay (no reasoning happens server-side); all transcription and reply generation happens in Gemini's Live API itself.

## Architecture (high level)

Browser (mic capture + local VAD + WebSocket client + TTS playback) sends binary audio frames (PCM16) and activity_start/activity_end control signals over a single WebSocket to the FastAPI backend, which acts purely as a relay — it does no reasoning itself. The backend forwards everything over a second, persistent WebSocket to the Gemini Live API, which transcribes speech, reasons about a reply, and generates both a spoken response and a text transcript. The reply streams back through the same path in reverse: backend to browser, buffered until complete, then spoken aloud.

## Project structure

app/api/websocket.py is the /ws endpoint that relays audio and control signals. app/config/settings.py loads GEMINI_API_KEY and GEMINI_MODEL from .env, while app/config/prompts.py holds the assistant's persona and system instruction. app/services/gemini_client.py owns the Gemini Live WebSocket session, and app/services/response_parser.py turns Gemini's raw events into simple type:content strings. On the frontend, app/static/js/app.js orchestrates the Start/Stop buttons and wires everything together, app/static/js/audio.js handles mic capture and local voice-activity detection, app/static/js/websocket.js is the WebSocket transport layer for both binary and text frames, and app/static/js/audio_output.js handles text-to-speech playback. app/static/worklets/recorder.worklet.js converts raw audio into PCM16 chunks, and app/static/index.html is the entry page. app/utils/logger.py provides shared logging. run.py is the uvicorn entry point, alongside requirements.txt and .env.example at the project root.

## Setup

Clone the project and enter the folder with git clone followed by cd into the fastapi-gemini-live-voice directory. Create a virtual environment with python -m venv venv, then activate it — venv\Scripts\activate on Windows or source venv/bin/activate on macOS/Linux — and install dependencies with pip install -r requirements.txt. Configure your API key by copying .env.example to .env, then edit .env and add your real GEMINI_API_KEY, which you can get at aistudio.google.com/apikey. Never commit your real .env file — it's already excluded via .gitignore. Finally, run the server with python run.py, then open http://localhost:8000/static/index.html in your browser, click Start, and talk.

## How turn-taking works

Gemini's own automatic voice-activity detection is disabled (automatic_activity_detection.disabled = True in the setup handshake). Instead, the browser's local VAD explicitly signals activity_start and activity_end based on real-time volume detection with hysteresis — this was a deliberate fix for duplicate and inconsistent replies that occurred under Gemini's default automatic detection.

## Notes on the free tier

Gemini's free API tier enforces limits on requests per minute and concurrent Live sessions, shared across your entire Google Cloud project, not per API key. This project is built for personal and demo use — scaling to many concurrent users requires enabling billing and adding connection-level safeguards not included here.
