"""
Converts raw PCM audio (as returned by Gemini's TTS API) into OGG/Opus —
the only format WhatsApp renders as a real "voice note" (mic icon,
waveform, playback speed control). Any other format sends as a plain file
attachment instead.

Requires ffmpeg installed and available on PATH.
"""
import subprocess
from app.services.tts import PCM_SAMPLE_RATE


def pcm_to_ogg_opus(pcm_bytes: bytes) -> bytes:
    process = subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "s16le", "-ar", str(PCM_SAMPLE_RATE), "-ac", "1",
            "-i", "pipe:0",
            "-c:a", "libopus",
            "-f", "ogg",
            "pipe:1",
        ],
        input=pcm_bytes,
        capture_output=True,
    )
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {process.stderr.decode(errors='ignore')}")
    return process.stdout
