"""Wake word -> STT -> agent -> TTS voice loop."""
from agent.graph import build_graph
from agent.voice.stt import record_and_transcribe
from agent.voice.tts import speak
from agent.voice.wake_word import wait_for_wake_word

def run_voice_loop():
    app=build_graph(); history=[]
    print("Jarvis voice mode. Say the wake word to begin.")
    while True:
        if not wait_for_wake_word(): continue
        text=record_and_transcribe()
        if not text: continue
        if text.lower() in {"stop","exit","quit"}:
            speak("Goodbye."); break
        history.append({"role":"user","content":text})
        result=app.invoke({"messages":history,"iterations":0}); history=result["messages"]
        reply=getattr(history[-1],"content",str(history[-1])); print(f"jarvis> {reply}"); speak(reply)
