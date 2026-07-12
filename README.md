# Voice Assistant Agents

This repository contains two real-time, voice-to-voice assistant implementations built with FastAPI and the Google Gemini Live API.

## Project Overview

| Project | Description |
| :--- | :--- |
| **[Gemini Live Voice](fastapi-gemini-live-voice/)** | A low-latency, real-time voice assistant with barge-in support and client-side VAD. |
| **[Gemini Live Voice with RAG](fastapi-gemini-live-rag/)** | The base assistant extended with RAG functionality for fact-based, context-aware document querying. |

---

## Shared Features
* **Persistent WebSockets:** Uses BidiGenerateContent for real-time, streaming audio.
* **Client-Side VAD:** Browser-based voice activity detection (VAD) with hysteresis to eliminate phantom replies.
* **Barge-in Support:** Enables natural, human-like conversation where the assistant stops immediately when you speak.
* **FastAPI Backend:** Lightweight relay architecture for minimal latency.

## Prerequisites
* Python 3.10+
* A Google Gemini API Key ([Get it here](https://aistudio.google.com/apikey))

---

*Note: These projects are designed for demo purposes. See individual project folders for setup and usage instructions.*