"""Offline text-to-speech with Kokoro."""
import numpy as np
from agent import config

def speak(text: str) -> None:
    try:
        import sounddevice as sd
        from kokoro_onnx import Kokoro
        k=Kokoro()
        samples, rate=k.create(text, voice=config.TTS_VOICE, speed=1.0, lang='en-us')
        sd.play(np.asarray(samples), rate); sd.wait()
    except Exception as e:
        print(f"[tts] {e}")
