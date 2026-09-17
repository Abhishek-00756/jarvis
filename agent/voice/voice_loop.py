"""Ties wake word -> STT -> agent graph -> TTS into a hands-free loop.

Run with: python -m agent.main --voice
"""

import time

from agent.graph import build_graph
from agent.voice.stt import record_and_transcribe
from agent.voice.tts import speak
from agent.voice.wake_word import WakeWordListener


def run_voice_loop():
    app = build_graph()
    history: list = []

    def on_wake():
        nonlocal history
        text = record_and_transcribe()
        if not text:
            return
        if text.strip().lower() in {"stop", "exit", "quit", "goodbye"}:
            speak("Goodbye.")
            raise SystemExit

        history.append({"role": "user", "content": text})
        result = app.invoke({"messages": history, "iterations": 0})
        history = result["messages"]

        final_message = history[-1]
        content = getattr(final_message, "content", str(final_message))
        print(f"jarvis> {content}")
        speak(content)

    listener = WakeWordListener(on_wake=on_wake)
    listener.start()
    print("Voice mode active. Say the wake word, then speak your request.")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(0.1)
    except (KeyboardInterrupt, SystemExit):
        listener.stop()
        print("\nVoice loop stopped.")
