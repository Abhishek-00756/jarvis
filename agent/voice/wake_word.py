"""Simple openWakeWord listener."""
import numpy as np
import sounddevice as sd
from agent import config

def wait_for_wake_word():
    try:
        from openwakeword.model import Model
        model=Model(wakeword_models=[config.WAKE_WORD])
        block=1280
        print(f"[wake] Waiting for '{config.WAKE_WORD}'...")
        while True:
            audio=sd.rec(block,samplerate=config.SAMPLE_RATE,channels=1,dtype='int16'); sd.wait()
            scores=model.predict(audio.reshape(-1))
            if max(scores.values(),default=0) > 0.5: return True
    except Exception as e:
        print(f"[wake] {e}"); return False
