"""Speech-to-text using MLX-Whisper (Apple Silicon native).

record_and_transcribe() records from the default microphone until a
silence gap is detected, then transcribes the recording. This is the
simplest reliable pattern for a push/wake-to-talk assistant; swap the
silence-detection heuristic for webrtcvad if you want tighter barge-in
behavior later.
"""

import numpy as np
import sounddevice as sd

from agent import config

SILENCE_THRESHOLD = 500       # RMS amplitude below this counts as silence
SILENCE_DURATION_S = 1.2      # stop recording after this much continuous silence
MAX_RECORD_S = 20


def _record_until_silence() -> np.ndarray:
    print("[stt] Listening...")
    chunks = []
    silence_chunks_needed = int(SILENCE_DURATION_S * config.SAMPLE_RATE / 1024)
    silent_run = 0
    max_chunks = int(MAX_RECORD_S * config.SAMPLE_RATE / 1024)

    with sd.InputStream(
        samplerate=config.SAMPLE_RATE, channels=1, dtype="int16", blocksize=1024
    ) as stream:
        for _ in range(max_chunks):
            data, _ = stream.read(1024)
            chunks.append(data.copy())
            rms = np.sqrt(np.mean(data.astype(np.float32) ** 2))
            if rms < SILENCE_THRESHOLD:
                silent_run += 1
                if silent_run >= silence_chunks_needed and len(chunks) > 5:
                    break
            else:
                silent_run = 0

    return np.concatenate(chunks).flatten()


def record_and_transcribe() -> str:
    """Record from the mic and return the transcribed text."""
    import mlx_whisper

    audio = _record_until_silence()
    audio_float = audio.astype(np.float32) / 32768.0

    result = mlx_whisper.transcribe(audio_float, path_or_hf_repo=config.STT_MODEL)
    text = result.get("text", "").strip()
    print(f"[stt] Heard: {text}")
    return text
