"""Speech-to-text using MLX-Whisper on Apple Silicon."""
import numpy as np
import sounddevice as sd
from agent import config
SILENCE_THRESHOLD=500
SILENCE_DURATION_S=1.2
MAX_RECORD_S=20

def _record_until_silence():
    frames=[]; chunk=1600; silent=0
    for _ in range(int(MAX_RECORD_S*config.SAMPLE_RATE/chunk)):
        audio=sd.rec(chunk,samplerate=config.SAMPLE_RATE,channels=1,dtype='int16'); sd.wait()
        frames.append(audio.copy())
        rms=float(np.sqrt(np.mean(audio.astype(np.float32)**2)))
        silent = silent + chunk/config.SAMPLE_RATE if rms < SILENCE_THRESHOLD else 0
        if len(frames)>2 and silent >= SILENCE_DURATION_S: break
    return np.concatenate(frames).reshape(-1).astype(np.float32)/32768.0

def record_and_transcribe():
    import mlx_whisper
    audio=_record_until_silence()
    result=mlx_whisper.transcribe(audio, path_or_hf_repo=config.STT_MODEL)
    return result.get('text','').strip()
