![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![LiveKit](https://img.shields.io/badge/LiveKit_Agents-~1.5-7B61FF?style=flat-square)
![Gemini](https://img.shields.io/badge/Gemini-Live_API-4285F4?style=flat-square&logo=google&logoColor=white)
![uv](https://img.shields.io/badge/uv-latest-DE5FE9?style=flat-square)
![BVC](https://img.shields.io/badge/BVC-Noise_Cancellation-2EA44F?style=flat-square)

# 🎙️ Voice Sales Agent

**Autonomous B2B Voice Agent · Gemini Realtime · LiveKit · SIP-Ready**

---

## What is this?

An autonomous B2B voice sales agent built on LiveKit Agents and Gemini Live API. Defaults to native speech-to-speech — no separate STT/TTS/VAD pipeline. Alternatively supports a classic STT → LLM → TTS pipeline (e.g. Deepgram + GPT-4 + Cartesia) via `AgentSession` configuration. Handles outbound sales conversations with configurable personality and instructions, with telephony integration via SIP (e.g. Twilio).

---

## Architecture

```
Agent Process (agent.py)
├── AgentServer (@rtc_session)
├── AgentSession
│   └── google.realtime.RealtimeModel (Gemini Live)
│       ├── Native Speech-to-Speech
│       ├── Affective Dialog (tone adapts to caller)
│       └── Built-in VAD + Turn Detection
├── BVC Noise Cancellation
└── Metrics (UsageCollector + Event Handlers)
```

```
LiveKit Cloud / SIP Trunk → AgentSession → RealtimeModel → Voice Response
```

---

## Tech Stack

| Tech | Version | Purpose |
|------|---------|---------|
| Python | 3.13 | Runtime |
| LiveKit Agents SDK | ~1.5 | Voice agent framework, WebRTC, session lifecycle |
| Gemini Live API | RealtimeModel | Native speech-to-speech, affective dialog, built-in VAD |
| livekit-plugins-noise-cancellation | >=0.2.5 | BVC telephony-grade noise suppression |
| python-dotenv | >=1.2.2 | Environment configuration |
| uv | latest | Package management, deterministic lockfile |

---

## Project Structure

```
voiceagent_test2.0/
├── livekit-voice-agent/
│   ├── agent.py              # Agent entrypoint: server, session, prompt, metrics
│   ├── pyproject.toml        # Dependencies and project metadata
│   └── uv.lock               # Deterministic dependency lockfile
├── .claude/
│   └── agents/
│       ├── livekit-expert.md  # Claude Code sub-agent for LiveKit research
│       └── twilio-expert.md   # Claude Code sub-agent for Twilio guidance
├── .gitignore
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- LiveKit Cloud account
- Gemini API key with Live API access

### Setup

```bash
git clone https://github.com/kelbmodus/voiceagent_test2.0.git
cd voiceagent_test2.0/livekit-voice-agent
uv sync
cp .env.example .env
# Fill in LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, GOOGLE_API_KEY
```

### Run

```bash
# Console (local dev, speak into mic)
uv run python agent.py console

# LiveKit Cloud (connects to cloud, test via Agents Playground)
uv run python agent.py start
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit Cloud project URL |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `GOOGLE_API_KEY` | Gemini API key with Live API access |

---

## Telephony

The agent supports outbound calls via LiveKit SIP integration. Connect a SIP trunk provider (e.g. Twilio) to LiveKit Cloud for PSTN connectivity. Use `BVCTelephony` noise cancellation mode for SIP calls.

---

## Metrics & Observability

Built-in metrics via LiveKit `UsageCollector`. Tracks agent state transitions, user transcripts, conversation items, and token usage. Extensible to external observability platforms.

---

## Constraints

- `load_dotenv()` must precede all LiveKit imports
- Always use `uv run` — never invoke `python` directly
- Model configuration belongs in `agent.py` + `.env` only
- `.env` is gitignored — never commit secrets
- Port 8081 must be free for cloud mode
