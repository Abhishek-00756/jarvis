"""Persist conversation history between runs."""
import json, os
from pathlib import Path
from agent import config, memory
SESSION_FILE = os.path.join(config.MEMORY_PATH, "session_history.json")
MAX_MESSAGES_BEFORE_SUMMARY = 40
KEEP_RECENT_MESSAGES = 20

def _to_plain(messages):
    plain=[]
    for m in messages:
        if isinstance(m, dict): role, content=m.get("role"), m.get("content")
        else:
            msg_type=getattr(m,"type",None); content=getattr(m,"content",None)
            role={"human":"user","ai":"assistant"}.get(msg_type,msg_type)
        if role in ("user","assistant") and content: plain.append({"role":role,"content":content})
    return plain

def load_history():
    if not os.path.exists(SESSION_FILE): return []
    try:
        with open(SESSION_FILE) as f: return json.load(f)
    except (json.JSONDecodeError,OSError): return []

def save_history(messages):
    Path(config.MEMORY_PATH).mkdir(parents=True,exist_ok=True)
    with open(SESSION_FILE,"w") as f: json.dump(_to_plain(messages),f,indent=2)

def maybe_summarize(messages):
    plain=_to_plain(messages)
    if len(plain) <= MAX_MESSAGES_BEFORE_SUMMARY: return plain
    return plain[-KEEP_RECENT_MESSAGES:]
