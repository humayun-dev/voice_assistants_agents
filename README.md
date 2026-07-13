# Voice Assistant Agents

This repository contains real-time, voice-to-voice assistant implementations and communication agents built with FastAPI and the Google Gemini API.

## Project Overview

| Project | Description |
| :--- | :--- |
| [**Gemini Live Voice**](gemini_live_voice/) | A low-latency, real-time voice assistant with barge-in support and client-side VAD. |
| [**Gemini Live Voice w/ RAG**](gemini_live_voice_rag/) | The base assistant extended with RAG functionality for fact-based, context-aware document querying. |
| [**WhatsApp Business Agent**](whatsapp_business_agent/) | A conversational agent integrated with WhatsApp for automated business interactions and service handling. |

## Shared Features

* **Persistent WebSockets:** Uses BidiGenerateContent for real-time, streaming audio and data processing.
* **Client-Side VAD:** Browser-based voice activity detection (VAD) with hysteresis to eliminate phantom replies.
* **Barge-in Support:** Enables natural, human-like conversation where the assistant stops immediately when you speak.
* **FastAPI Backend:** Lightweight relay architecture for minimal latency.

## Project Directories

* [/gemini_live_voice](gemini_live_voice/): Core voice assistant implementation.
* [/gemini_live_voice_rag](gemini_live_voice_rag/): Voice assistant with retrieval-augmented generation.
* [/whatsapp_business_agent](whatsapp_business_agent/): Automated WhatsApp messaging agent.

## Prerequisites

* Python 3.10+
* A Google Gemini API Key ([Get it here](https://aistudio.google.com/))
* Environment-specific dependencies (see individual project `requirements.txt` files)

> **Note:** These projects are designed for demo purposes. Please see the individual project folders for specific setup, configuration, and usage instructions.