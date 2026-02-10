import os
import json
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI

from deepgram import DeepgramClient

load_dotenv()

# --- Keys (loaded from .env) ---
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
DEEPGRAM_API_KEY = os.environ["DEEPGRAM_API_KEY"]
ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

# --- File paths ---
AUDIO_IN = "assets/audio_input/sample.m4a"     # <-- using your .m4a
LOG_PATH = "logs/turns.jsonl"                  # <-- log file
OUT_DIR = Path("outputs/audio_reply")

# --- OpenAI settings ---
MODEL = "gpt-4.1-mini"
SYSTEM_INSTRUCTIONS = "You are a helpful voice assistant. Reply in 1-2 short sentences."

# --- Deepgram settings ---
DEEPGRAM_MODEL = "nova-3"

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

# -----------------------
# LOG WRITER (JSONL)
# -----------------------
def log_record(record: dict):
    Path("logs").mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
      f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n") # <-- THIS WRITES LOGS

def transcribe_with_deepgram(audio_path: str) -> dict:
    dg = DeepgramClient(api_key=DEEPGRAM_API_KEY)

    with open(audio_path, "rb") as af:
        audio_bytes = af.read()

    t0 = time.time()
    resp = dg.listen.v1.media.transcribe_file(
        request=audio_bytes,
        model=DEEPGRAM_MODEL,
        smart_format=True,
        punctuate=True,
    )
    stt_ms = int((time.time() - t0) * 1000)

    transcript = resp.results.channels[0].alternatives[0].transcript
    return {"transcript": transcript, "stt_ms": stt_ms, "deepgram_model": DEEPGRAM_MODEL}

def generate_reply_with_openai(user_text: str) -> dict:
    client = OpenAI(api_key=OPENAI_API_KEY)

    t0 = time.time()
    resp = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {"role": "user", "content": user_text},
        ],
        temperature=0.2,
        max_output_tokens=120,
    )
    llm_ms = int((time.time() - t0) * 1000)

    return {
        "reply_text": resp.output_text,
        "llm_ms": llm_ms,
        "openai_response_id": getattr(resp, "id", None),
        "openai_usage": getattr(resp, "usage", None),
    }

def synthesize_with_elevenlabs(text: str) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {"text": text}

    t0 = time.time()
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    tts_ms = int((time.time() - t0) * 1000)

    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs error {r.status_code}: {r.text}")

    out_file = OUT_DIR / f"reply_{int(time.time())}.mp3"
    out_file.write_bytes(r.content)

    return {"tts_ms": tts_ms, "audio_file": str(out_file), "elevenlabs_voice_id": ELEVENLABS_VOICE_ID}

def main():
    turn_id = f"turn_{int(time.time())}"
    t0_total = time.time()

    stt = transcribe_with_deepgram(AUDIO_IN)
    llm = generate_reply_with_openai(stt["transcript"])
    tts = synthesize_with_elevenlabs(llm["reply_text"])

    end_to_end_ms = int((time.time() - t0_total) * 1000)

    record = {
        "ts": now_iso(),
        "turn_id": turn_id,
        "audio_in": AUDIO_IN,
        "stt": stt,
        "llm": llm,
        "tts": tts,
        "end_to_end_ms": end_to_end_ms,
    }

    log_record(record)

    print(f"Wrote logs to: {LOG_PATH}")
    print(f"Transcript: {stt['transcript']}")
    print(f"Reply: {llm['reply_text']}")
    print(f"Audio saved: {tts['audio_file']}")
    print(f"End-to-end: {end_to_end_ms} ms")

if __name__ == "__main__":
    main()
