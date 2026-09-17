"""Text-to-speech using Kokoro (ONNX, fully local, no API key).

If you'd rather use Piper instead of Kokoro, swap the body of speak() —
keep the same function signature so voice_loop.py doesn't need to change.
"""

import sounddevice as sd

from agent import config

_kokoro = None


def _get_kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro

        _kokoro = Kokoro("kokoro-v0_19.onnx", "voices.bin")
    return _kokoro


def speak(text: str) -> None:
    """Synthesize and play `text` aloud through the default output device."""
    if not text:
        return
    kokoro = _get_kokoro()
    samples, sample_rate = kokoro.create(text, voice=config.TTS_VOICE, speed=1.0)
    sd.play(samples, sample_rate)
    sd.wait()
