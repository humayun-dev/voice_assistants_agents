# Gemini Live Voice Assistant with RAG

A real-time, voice-to-voice assistant built on **FastAPI** and **Google's Gemini Live API**, extended with Retrieval-Augmented Generation (RAG). Talk to it naturally through your browser — it listens, decides on its own whether a question needs looking up in a real reference document, and replies out loud, with support for interrupting it mid-sentence like a real conversation.

## Features

- **Real-time voice conversation** over a persistent WebSocket connection to Gemini's Live API (`BidiGenerateContent`), not request/response HTTP.
- **Client-side voice activity detection (VAD)** — the browser decides exactly when the user starts and stops talking (local RMS volume + hysteresis), and drives Gemini's turn boundaries explicitly rather than relying on server-side automatic detection. This avoids the duplicate/phantom replies that automatic detection can produce.
- **Barge-in / interruption support** — talking over the assistant while it's speaking cuts it off immediately and hands control back to the user right away.
- **Retrieval-Augmented Generation (RAG)** — a search_leave_rules tool is declared to Gemini via native function calling. Gemini decides per turn whether a question needs a real lookup, such as how much sick leave someone gets, or can be answered conversationally, such as a simple greeting. Retrieval runs against a small in-process vector index, with no external database server required, built from a plain text reference document.
- **Clean separation of concerns** — the backend never runs any reasoning itself; it relays audio and control signals to Gemini and transparently handles Gemini's tool calls for document lookups behind the scenes.

## Architecture (high level)

Browser (mic capture + local VAD + WebSocket client + TTS playback) sends binary audio frames (PCM16) and activity_start/activity_end control signals over a single WebSocket to the FastAPI backend, which acts purely as a relay. The backend forwards everything over a second, persistent WebSocket to the Gemini Live API. When Gemini decides a question needs grounding in the reference document, it pauses and sends a toolCall back to the backend, which embeds the query, runs a cosine-similarity search against pre-embedded document chunks, and sends the top matches back as a tool response, all invisible to the browser. Gemini then resumes generating its reply, grounded in that retrieved text, and the reply streams back through the same path in reverse: backend to browser, buffered until complete, then spoken aloud.

## Project structure

app/api/websocket.py is the /ws endpoint that relays audio and control signals. app/config/settings.py loads GEMINI_API_KEY and GEMINI_MODEL from .env, app/config/prompts.py holds the assistant's persona and tool-usage instructions, app/config/leave_rules.txt is the plain text reference document used for retrieval, and app/config/leave_rules_index.json is the generated embedding index, which is gitignored and rebuilt locally. app/services/gemini_client.py owns the Gemini Live WebSocket session and declares the search tool while handling tool calls, app/services/embedding_client.py calls Gemini's embedding model using the same API key as voice, app/services/vector_store.py handles chunking, index build and load, and similarity search, and app/services/response_parser.py turns Gemini's raw events into simple type:content strings. On the frontend, app/static/js/app.js orchestrates the Start/Stop buttons and wires everything together, app/static/js/audio.js handles mic capture and local voice-activity detection, app/static/js/websocket.js is the WebSocket transport layer for both binary and text frames, and app/static/js/audio_output.js handles text-to-speech playback. app/static/worklets/recorder.worklet.js converts raw audio into PCM16 chunks, and app/static/index.html is the entry page. app/utils/logger.py provides shared logging. scripts/build_index.py is a one-time script that embeds the reference document into the searchable index, and scripts/extract_pdf.py is a reusable utility for extracting text from a source PDF. run.py is the uvicorn entry point, alongside requirements.txt and .env.example at the project root.

## Setup

Clone the project and enter the folder with git clone followed by cd into the project directory. Create a virtual environment with python -m venv venv, then activate it — venv\Scripts\activate on Windows or source venv/bin/activate on macOS/Linux — and install dependencies with pip install -r requirements.txt. Configure your API key by copying .env.example to .env, then edit .env and add your real GEMINI_API_KEY, which you can get at aistudio.google.com/apikey. Never commit your real .env file — it's already excluded via .gitignore. Before starting the server for the first time, build the RAG index by running python scripts/build_index.py, which requires network access and reads your real API key; this only needs to be rerun when leave_rules.txt changes. Finally, run the server with python run.py, then open http://localhost:8000/static/index.html in your browser, click Start, and talk.

## How turn-taking works

Gemini's own automatic voice-activity detection is disabled (automatic_activity_detection.disabled = True in the setup handshake). Instead, the browser's local VAD explicitly signals activity_start and activity_end based on real-time volume detection with hysteresis — this was a deliberate fix for duplicate and inconsistent replies that occurred under Gemini's default automatic detection.

## How the RAG lookup works

The reference document is chunked once, offline, by scripts/build_index.py, and each chunk is embedded into a vector using Gemini's embedding model. At query time, the user's question is embedded the same way, and compared against every stored chunk using cosine similarity; the top matches are returned to Gemini as the result of its tool call. This whole exchange happens as an internal round trip between the backend and Gemini and is never visible to the user or the browser. For general conversation, Gemini skips this process entirely and answers directly.

## Notes on the free tier

Gemini's free API tier enforces limits on requests per minute and concurrent Live sessions, shared across your entire Google Cloud project, not per API key. Both voice and embedding calls draw from this same shared quota. This project is built for personal and demo use — scaling to many concurrent users requires enabling billing and adding connection-level safeguards not included here.