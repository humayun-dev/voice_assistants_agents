# Project Journey: WhatsApp Business Multi-Agent AI Assistant

A complete record of how this project was designed, debugged, and built —
kept in chronological order so the *reasoning* behind each decision isn't lost,
not just the final code.

---

## Phase 1 — Finding the right idea

**Started with:** a request for a genuinely unique LangGraph multi-agent
project — explicitly *not* another "research summarizer" or generic
customer-support-bot tutorial clone.

**Ideas explored and why most were rejected:**
- *Land Fraud Red Team* (Pakistan property due-diligence, adversarial
  Skeptic/Judge agents) — strong concept, saved for later; required domain
  knowledge Khan didn't have yet.
- *Socratic Adversary + Mastery Verifier* (education tutoring) — strong
  concept, ties into real UET work; also saved for later.
- *Career Application War-Room* — good fit (Khan already had the domain
  expertise from his own job applications).
- *Multi-Agent Customer Support* (Intent → Billing/Refund/Escalation
  agents) — **rejected**: this is the textbook example in LangGraph's own
  docs and every agent-framework tutorial. Too generic to differentiate.
- Voice-call agent using **Vapi/Retell** — explored in depth, then rejected
  once the real economics became clear (see Phase 2).

**Key lesson from this phase:** a project idea's value isn't just "is this
useful" — it's "will this look like I followed a tutorial." Adversarial /
debate-pattern agents (Skeptic vs Advocate, Challenger vs Tutor) were
identified as a stronger differentiator than simple routing pipelines.

---

## Phase 2 — The voice-call detour (and why it was abandoned)

**Explored:** using Vapi or Retell (voice-AI SaaS platforms) to build a
phone-call-based agent.

**Why it was dropped:**
- Both are genuinely paid — Vapi's advertised $0.05/min is *just*
  orchestration; STT, LLM, and TTS are billed separately on top, landing
  real cost around $0.20–0.33/min.
- Realized Khan already had a working real-time voice pipeline
  (`fastapi-gemini-live-voice`, built earlier) using Gemini Live natively —
  paying for Vapi/Retell would mean re-buying capability already built.
- The cheaper DIY alternative (**Twilio Media Streams** bridged to his own
  Gemini Live pipeline) was designed in detail: Twilio handles the raw
  phone line, his own FastAPI service handles STT/TTS/reasoning via Gemini
  Live's native audio + built-in server-side VAD (no need to hand-roll
  turn-taking).
- **Real blocker discovered:** Twilio doesn't sell local Pakistani phone
  numbers. Testing would require an international number, meaning calling
  it from Khan's own Ufone SIM would incur real international call charges
  just to test his own project.
- A "click-to-call from a browser" (WebRTC) alternative was proposed to
  dodge the phone-number problem, but rejected because it undercuts the
  entire point: proving genuine telephony integration, which is what makes
  a voice-call project credible to a technical reviewer.

**Follow-on idea (also explored, also rejected):** a voice agent that
searches live websites/Facebook pages for real-time hotel/tourism data.
Killed for two structural reasons:
1. **Latency physics** — live scraping (rendering a page, parsing it) takes
   3–10+ seconds; a live phone call needs a reply in under ~1–2 seconds or
   it feels broken. This isn't a bug to fix, it's incompatible with the
   medium.
2. **Facebook ToS** — programmatic scraping of Facebook pages, even public
   ones, generally violates their Terms of Service and gets actively
   blocked.

**Key lesson:** real production voice/financial agents (stock tickers,
airline bots) achieve "live" answers not through scraping, but through
**structured, low-latency APIs built for that exact purpose** — a
principle that directly informed the final architecture (Supabase as a
fast structured data source, not live scraping).

---

## Phase 3 — Landing on WhatsApp Business Automation

**The pivot:** away from live phone calls, toward WhatsApp — which sidesteps
the latency problem entirely (a few seconds of "typing..." feels completely
normal on WhatsApp, unlike dead air on a call) and is a genuinely common,
real workflow for Pakistani small businesses (shops running their entire
sales process manually through WhatsApp DMs today).

**Architecture designed:**
```
Customer message → Meta Webhook → FastAPI → LangGraph multi-agent graph
   → Intent Agent routes to → Catalog / Negotiation / Order / Escalation
   → Gemini-generated reply → WhatsApp Cloud API → Customer
```

---

## Phase 4 — Infrastructure setup (the part with the most real debugging)

### Meta Developer / Business setup
- Created a Meta Developer account and app (`WA-business-agent`).
- Hit a **Business Portfolio verification prompt** — clarified this is
  purely an internal admin container, never public-facing, and
  verification is only needed for public App Review or accessing other
  businesses' data — neither applies here, so it was safely skipped.
- Used Meta's **free sandbox test number** (no business verification
  needed) and verified Khan's own personal number as a test recipient
  (up to 5 allowed).

### Hosting — the free-tier hunt
- **Render:** hit a card-verification requirement even on the "Free" tier.
- **Hugging Face Spaces:** discovered Docker SDK had recently been gated
  behind payment for new free accounts (only Gradio/static remained free).
- **Resolution:** for a learning-purposes project, hosting doesn't need to
  be "production" — pivoted to running the FastAPI app locally and
  exposing it via **Cloudflare Tunnel** (`cloudflared`), which is genuinely
  free with no card required. Trade-off accepted: the tunnel URL changes
  on every restart (using the free "quick tunnel," not a named one), and
  the laptop must be running for the webhook to work.

### The webhook — three real bugs, in order encountered

1. **Verify token vs access token confusion** — pasted the long WhatsApp
   *access token* into the `WEBHOOK_VERIFY_TOKEN` slot by mistake. Fixed by
   separating them into two distinct `.env` variables.
2. **Callback URL missing `/webhook` suffix** — Meta's verification failed
   because the URL pointed at the tunnel's root (`/`) instead of the actual
   route.
3. **The "Shadow Delivery" bug (the big one):** Meta's dashboard "Test"
   button worked perfectly, but real messages sent from an actual phone
   never arrived — with no error shown anywhere. Root cause: **configuring
   a Callback URL at the App level is not enough; the WhatsApp Business
   Account (WABA) itself must be explicitly subscribed to the app**, via a
   separate API call:
   ```
   POST /{waba_id}/subscribed_apps
   ```
   This is a known, easy-to-miss gap in Meta's current dashboard UI.
   Diagnosed by checking `GET /{waba_id}/subscribed_apps` (returned empty),
   then fixed with the POST call in Graph API Explorer.

### Permanent authentication
- The default WhatsApp access token expires in 24 hours, causing a `401`
  failure mid-testing. Fixed permanently by creating a **System User** in
  Meta Business Settings and generating a **never-expiring token** scoped
  to `whatsapp_business_messaging` + `whatsapp_business_management`.

---

## Phase 5 — Stage 1: A single direct Gemini call (no agents yet)

Built the simplest possible loop first: webhook receives a message → one
Gemini call → reply sent back. Deliberately no memory, no routing — just to
prove the full chain worked end to end before adding complexity.

**Bugs hit:**
- Used `gemini-2.5-flash-native-audio-preview-12-2025` by mistake — this
  model only supports `bidiGenerateContent` (the real-time Live API), not
  `generateContent` (a normal one-shot text call). Wrong tool for the job.
- Switched to `gemini-2.5-flash` — got a 404 explaining that model is
  **"no longer available to new users"** (Google gates some model versions
  to only pre-existing projects). Fixed by using the `gemini-flash-latest`
  alias instead, which always points at Google's current recommended
  Flash model — a more future-proof choice than pinning exact version
  numbers on an actively-evolving model lineup.

---

## Phase 6 — Stage 2: LangGraph + per-customer memory

Introduced `langgraph`'s `MessagesState` and a `MemorySaver` checkpointer,
keyed by `thread_id = sender` (the customer's WhatsApp number) — meaning
every customer gets an isolated, remembered conversation automatically,
without hand-rolling session storage.

**Bugs hit:**
- A `protobuf`/`proto-plus` version mismatch crashed the app on import
  (`MessageToDict() got an unexpected keyword argument 'float_precision'`).
  Fixed by upgrading `proto-plus` and `langchain-google-genai` together.
- After the upgrade, newer `langchain-core` changed `AIMessage.content`
  from a plain string into a list of content blocks
  (`[{'type': 'text', 'text': '...', ...}]`). Sending that raw structure to
  WhatsApp's API caused a `400` (`text.body` must be a string). Fixed with
  an `extract_text()` helper that handles both the old and new formats.

**Verified working:** told the bot "My name is Khan," followed later by
"what's my name?" — it correctly remembered, per-customer, confirming the
checkpointer worked.

---

## Phase 7 — Stage 3: Real multi-agent routing

This is where it became a genuine multi-agent system rather than one node
calling an LLM. Built:
- An **Intent Agent** that classifies each message into `catalog`,
  `negotiation`, `order`, or `escalation`.
- LangGraph's `add_conditional_edges` to route to one of four specialist
  agent nodes based on that classification — the actual structural
  difference between "multi-agent" and "multiple prompts."
- Each specialist given its own constraints: Catalog grounded in real
  product data, Negotiation capped at a fixed discount ceiling, Order
  collecting structured details, Escalation deferring to a human owner.

**All four routes tested and confirmed working** — including the
escalation path correctly logging an `[OWNER ALERT]`.

**Important bug caught during testing — the "prompt leak":** the
Escalation Agent's system prompt explicitly said *"do not promise
discounts or specifics,"* but under the emotional pull of a real complaint
message, Gemini ignored that instruction anyway and offered a discount on
its own initiative.

**Fix — enforced in code, not just prompted:** the LLM still generates an
empathetic sentence, but before it ever reaches the customer, a regex
checks it for pricing/discount/refund language. If found, the risky
sentence is discarded and replaced with a safe, fixed fallback. **Lesson:
a system prompt is a strong suggestion, not a hard constraint — anything
that must always hold needs to be enforced in code.**

---

## Phase 8 — Stage 4: Real data via Supabase

Replaced the hardcoded product list with a live Postgres-backed catalog.

- Created a `products` table (`name`, `price`, `stock`, `description`)
  through Supabase's Table Editor, with Row Level Security left **on**
  (not disabled as a shortcut).
- Used Supabase's newer **secret key** (`sb_secret_...`) rather than the
  old `service_role` key — appropriate since the FastAPI backend is a
  trusted server context, and the secret key bypasses RLS safely there.
- Every specialist agent (Catalog, Negotiation, Order) now calls
  `get_catalog_text()`, which queries the real table live on every
  message — **verified by editing a price directly in Supabase's
  dashboard and confirming the bot reflected the new price on the very
  next message, without a server restart.**

---

## Phase 9 — Professional folder restructuring

The entire project had been living in a single `main.py`. Refactored into
a layered structure with **zero logic changes** — a pure reorganization:

```
app/
├── main.py            FastAPI entrypoint
├── config.py            All environment variables, loaded once
├── llm.py               Shared Gemini client
├── api/webhook.py       The only file that touches Request/Response
├── services/            External integrations (WhatsApp, Supabase)
└── agents/               LangGraph state, graph wiring, one file per node
```

**Why this split:** adding a future agent (say, a Refund Agent) now means
creating one new file and a couple of lines in `graph.py` — not scrolling
through 250 mixed-concern lines to find the right spot.

---

## Phase 10 — Adding voice messages

Extended the system to understand and reply to **voice notes**, not just
typed text — without touching any of the agent logic itself.

### Voice-in (transcription)
- WhatsApp delivers voice notes only as a `media_id` — a real two-step
  fetch is required: ask Graph API for a temporary download URL, then
  fetch that URL for the actual audio bytes.
- Sent those bytes directly to Gemini (native multimodal audio input) to
  get a transcript **and** detect the spoken language (English / Urdu /
  Pashto / other) in one call, returned as structured JSON.
- The transcript is fed into the *exact same* LangGraph pipeline as a
  typed message — the agents never need to know whether the customer
  typed or spoke.

**Bug hit:** after switching models, `gemini-flash-latest` unexpectedly
resolved to `gemini-3.5-flash`, which has a very tight free-tier quota (20
requests/day) — quota exhausted almost immediately during testing. Fixed
by switching to `gemini-flash-lite-latest`, a lighter model with a much
higher free daily limit.

### Voice-out (spoken replies)
- Added Gemini's TTS model (`gemini-2.5-flash-preview-tts`) to synthesize
  speech from the reply text.
- **Critical format requirement discovered:** WhatsApp only renders a real
  "voice note" bubble (mic icon, waveform) for **OGG files encoded with
  the Opus codec** — nothing else gets that treatment. Gemini's TTS
  returns raw PCM, so **ffmpeg** was installed and used to convert
  PCM → OGG/Opus before uploading.
- Built the full outbound chain: synthesize → convert → upload to
  WhatsApp (`POST /{phone_number_id}/media`) → send as an audio message
  referencing the returned `media_id`.

**Design decision:** voice-out only triggers when the customer *sent*
voice **and** the detected language is English or Urdol — Pashto stays
transcribed-and-answered-in-text for now, since Gemini's Pashto TTS has
documented pronunciation quality issues that hadn't been personally
verified yet.

**Bugs hit and fixed, in order:**
1. **TTS returning `500 INTERNAL` errors** — confirmed via research to be
   a widely-reported instability in Gemini's TTS *preview* endpoints
   generally, not specific to this project. Mitigated with a short
   retry-with-backoff, and a `try/except` fallback that sends a text reply
   instead of leaving the customer with nothing if TTS still fails after
   retrying.
2. **The same voice note getting replied to two or three times** — caused
   by the voice pipeline (download → transcribe → synthesize → convert →
   upload → send) being slow enough that Meta's webhook timed out and
   **retried delivery of the same message**. Fixed with message-ID
   deduplication: an in-memory set tracking already-processed `wamid`
   values, skipped immediately on a repeat before any expensive work runs.
3. **Replies coming back in English even when the customer spoke
   Urdu/Pashto** — the specialist agents' system prompts had never been
   told to mirror the customer's language, so Gemini defaulted to English
   regardless of input. Fixed by adding an explicit "reply in the same
   language the customer used" instruction to every specialist agent's
   prompt (Catalog, Negotiation, Order, Escalation) — deliberately leaving
   the Escalation Agent's hardcoded safety-net fallback text in English,
   since translating a safety string risks introducing an unverified
   translation error into the one part of the system that must always be
   correct.

---

## Where the project stands now

A working multi-agent WhatsApp Business assistant that:
- Understands typed **and spoken** messages, in English, Urdu, and Pashto
- Routes intelligently between four specialist agents via LangGraph
  conditional edges
- Remembers each customer's conversation independently
- Grounds every product answer in a **live** Supabase database
- Enforces its safety rules (discount ceiling, no unauthorized promises)
  in code, not just prompts
- Replies with real WhatsApp voice notes in English/Urdu when the customer
  spoke first
- Survives WhatsApp's webhook retry behavior without duplicating replies
- Is organized as a real layered FastAPI project, not a single script

**Known, deliberately-documented limitations** (see the README's
"Known limitations & lessons" section): in-memory conversation
checkpointing, in-memory message deduplication, Pashto voice-out not yet
enabled, and TTS preview-endpoint instability — each one a real
engineering tradeoff made consciously, not an oversight.
