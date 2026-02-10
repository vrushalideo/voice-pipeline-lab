# Voice Pipeline Lab — Deepgram + OpenAI + ElevenLabs

Small reproducible voice AI pipeline lab that demonstrates:

- Speech-to-Text with Deepgram
- LLM response generation with OpenAI
- Text-to-Speech with ElevenLabs
- Structured JSONL logging
- Per-stage latency measurement
- Support-style observability

## Pipeline

Audio file → Deepgram STT → OpenAI reply → ElevenLabs TTS → audio output + logs

## Files

- `src/run_pipeline.py` — main pipeline runner
- `logs/turns.jsonl` — structured run logs (gitignored)
- `.env.example` — required environment variables template

## Setup

Create `.env` with:

OPENAI_API_KEY=...
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...

Install deps and run:

python src/run_pipeline.py

## Purpose

Built as a support/debug style lab to inspect API request/response behavior,
parameter effects, and end-to-end voice pipeline timing.

## Postman

This repo includes a Postman collection to reproduce API calls without running code.

- Collection: `postman/voice-pipeline-lab.postman_collection.json`
- Environment template: `postman/voice-pipeline-lab.postman_environment.example.json`

### Import steps
1. Postman → Import → select the collection JSON
2. Postman → Environments → Import → select the environment example JSON
3. Fill in:
   - `OPENAI_API_KEY`
   - `DEEPGRAM_API_KEY`
   - `ELEVENLABS_API_KEY`
4. Select the environment and run requests:
   - OpenAI (Responses API)
   - Deepgram (STT file upload)
   - ElevenLabs (TTS audio output)

