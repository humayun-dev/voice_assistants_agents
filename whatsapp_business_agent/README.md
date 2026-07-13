# WhatsApp Business Agent — Multi-Agent AI Shop Assistant

A multi-agent AI system that runs a small business's WhatsApp — answering
product questions, negotiating prices within set limits, taking orders, and
knowing when to hand off to a human. Understands both **typed and spoken
(voice note) messages**, in English and Urdu, and can reply with a real
voice message when the customer spoke first. Built with **LangGraph**,
**Gemini**, **FastAPI**, and **Supabase**, on the real WhatsApp Business
Cloud API — not a simulated chat widget.

## Why this exists

Most "AI customer support" demos are a single LLM call wearing a chatbot UI.
This project is a genuine multi-agent system: a routing agent classifies
intent, then hands off to one of four specialist agents, each with its own
constraints — including a discount ceiling that's enforced in *code*, not
just prompted for, because prompts alone don't reliably hold under pressure
(see [Known limitations & lessons](#known-limitations--lessons) below).

## Architecture

```
Customer message (WhatsApp: text OR voice note)
        │
        ▼
Meta Webhook ──▶ FastAPI /webhook
        │
        ├─ if voice: download media → Gemini transcription
        │             (also detects language: english/urdu/pashto/other)
        │
        ▼
┌───────────────────────────────────────────┐
│              Intent Agent                  │
│   classifies: catalog | negotiation |       │
│               order | escalation            │
└───────────────────────────────────────────┘
        │
        ├──▶ Catalog Agent      (grounded in live Supabase product data)
        ├──▶ Negotiation Agent  (hard discount ceiling, escalates beyond it)
        ├──▶ Order Agent        (collects order details, confirms total)
        └──▶ Escalation Agent   (hands off to the owner; code-enforced —
                                  cannot promise discounts/refunds itself)
        │
        ▼
Gemini-generated reply
        │
        ├─ if customer sent voice AND language is English/Urdu:
        │     Gemini TTS → PCM → ffmpeg → OGG/Opus → upload → send as
        │     a real WhatsApp voice note
        │
        └─ otherwise: sent as a normal text message
        │
        ▼
WhatsApp Cloud API ──▶ Customer
```

Each customer's conversation is tracked independently via LangGraph's
checkpointer, keyed by their WhatsApp number (`thread_id`), so the agent
remembers context across messages without mixing up different customers.

## Tech stack

| Layer | Tool |
|---|---|
| Agent orchestration | LangGraph |
| LLM / transcription / TTS | Google Gemini (`gemini-flash-latest`, `gemini-2.5-flash-preview-tts`) |
| Backend | FastAPI |
| Database | Supabase (Postgres) |
| Messaging | WhatsApp Business Cloud API (Meta) |
| Audio conversion | ffmpeg (PCM → OGG/Opus, required for WhatsApp voice notes) |
| Local tunneling (dev) | Cloudflare Tunnel |

## Project structure

```
app/
├── main.py                    FastAPI entrypoint
├── config.py                   All environment variables, loaded once
├── llm.py                      Shared Gemini chat client
├── api/
│   └── webhook.py              Webhook verification, message routing,
│                                 voice/text reply decision, deduplication
├── services/
│   ├── whatsapp.py             Sending text + audio messages
│   ├── media.py                Downloading/uploading WhatsApp media
│   ├── transcription.py        Voice note → text + language detection
│   ├── tts.py                  Text → speech (Gemini TTS, with retry)
│   ├── audio_convert.py        PCM → OGG/Opus conversion via ffmpeg
│   └── supabase_client.py      Live product catalog queries
└── agents/
    ├── state.py                Shared LangGraph state schema
    ├── graph.py                 Wires all agent nodes together
    ├── utils.py                  Shared helpers
    └── nodes/
        ├── intent.py
        ├── catalog.py
        ├── negotiation.py
        ├── order.py
        └── escalation.py
```

## Setup

1. Install [ffmpeg](https://www.gyan.dev/ffmpeg/builds/) and confirm it's on
   your PATH (`ffmpeg -version`) — required for voice replies.
2. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in real values:
   - `WEBHOOK_VERIFY_TOKEN` — any string you choose, must match Meta's dashboard
   - `WHATSAPP_ACCESS_TOKEN` — a **permanent** System User token (not the 24h default)
   - `WHATSAPP_PHONE_NUMBER_ID`, from Meta's WhatsApp API Setup page
   - `GEMINI_API_KEY`, from Google AI Studio
   - `SUPABASE_URL` and `SUPABASE_SECRET_KEY`, from your Supabase project settings
4. In Supabase, create a `products` table with columns: `name` (text), `price` (int8), `stock` (int8), `description` (text).
5. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```
6. Expose it publicly for Meta's webhook (development: Cloudflare Tunnel; production: any always-on host):
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```
7. In Meta's App Dashboard → WhatsApp → Configuration, set the Callback URL to `<your-public-url>/webhook`, subscribe to the `messages` field, and **subscribe the app to your WABA** via the Graph API (`POST /{waba_id}/subscribed_apps`) — this step is easy to miss and silently breaks real message delivery even when everything else looks correct.

## Known limitations & lessons

Documented honestly, since these were real engineering problems, not just
setup steps:

- **The WABA→App subscription gap.** Configuring a webhook URL in Meta's
  dashboard is not enough — the WhatsApp Business Account itself must be
  explicitly subscribed to the app (`POST /{waba_id}/subscribed_apps`), or
  real messages silently never arrive while the dashboard's "Test" button
  still works, making it look like the integration is broken when it isn't.
- **Prompt instructions are not hard constraints.** The Escalation Agent's
  system prompt explicitly said not to offer discounts or refunds — Gemini
  ignored it under the emotional pull of a complaint message. The fix was a
  code-level regex check that discards any LLM output containing
  pricing/discount language and substitutes a safe, fixed response instead.
  Anything that must *always* hold should be enforced in code, not prompted.
- **Webhook retries can duplicate slow responses.** The voice pipeline
  (download → transcribe → synthesize → convert → upload → send) is slow
  enough that Meta sometimes retries the webhook delivery before the first
  attempt finishes, causing the same voice note to be processed multiple
  times. Fixed with message-ID deduplication — currently an in-memory set,
  which resets on restart and grows unbounded; a production version would
  use Redis or Supabase with a TTL instead.
- **Gemini's TTS is a preview endpoint with known intermittent 500 errors**
  (a widely reported issue, not specific to this project). Mitigated with a
  short retry-with-backoff, and if it still fails, the customer gets a text
  reply instead of nothing — voice is a best-effort enhancement, never a
  point of failure.
- **Voice replies are English/Urdu only for now.** Pashto voice notes are
  still transcribed and answered correctly, but the *reply* stays as text
  until Pashto TTS pronunciation quality has been properly verified (early
  testing showed known mispronunciation issues).
- **In-memory conversation checkpointing.** The current `MemorySaver()`
  checkpointer keeps conversation history in RAM — it resets on every
  restart. A Postgres-backed checkpointer (using the same Supabase project)
  is the natural next step for persistence.

