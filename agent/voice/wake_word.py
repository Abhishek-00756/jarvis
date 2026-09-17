"""Wake word detection using openWakeWord.

Runs continuously on a background thread listening for the configured wake
word (default "hey_jarvis"), at near-zero CPU cost. When detected, calls
the provided `on_wake` callback — the voice loop uses this to start
recording the user's actual request.
"""

import queue
import threading

import numpy as np
import sounddevice as sd
from openwakeword.model import Model

from agent import config

_FRAME_SAMPLES = 1280  # openWakeWord expects 80ms frames at 16kHz


class WakeWordListener:
    def __init__(self, on_wake, wake_word: str = None):
        self.on_wake = on_wake
        self.wake_word = wake_word or config.WAKE_WORD
        self.model = Model(wakeword_models=[self.wake_word])
        self._audio_q: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def _audio_callback(self, indata, frames, time_info, status):
        self._audio_q.put(indata.copy())

    def _listen_loop(self):
        with sd.InputStream(
            samplerate=config.SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=_FRAME_SAMPLES,
            callback=self._audio_callback,
        ):
            while not self._stop_event.is_set():
                frame = self._audio_q.get()
                prediction = self.model.predict(frame.flatten())
                score = prediction.get(self.wake_word, 0.0)
                if score > 0.5:
                    self.on_wake()

    def start(self):
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print(f"[wake_word] Listening for '{self.wake_word}'...")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
