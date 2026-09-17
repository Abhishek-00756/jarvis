"""Persists conversation history to disk between runs."""
import json,os
from pathlib import Path
from agent import config,memory
SESSION_FILE=os.path.join(config.MEMORY_PATH,"session_history.json")
MAX_MESSAGES_BEFORE_SUMMARY=40; KEEP_RECENT_MESSAGES=20
def _to_plain(messages:list)->list[dict]:
    plain=[]
    for m in messages:
        if isinstance(m,dict):role,content=m.get("role"),m.get("content")
        else:
            msg_type=getattr(m,"type",None);content=getattr(m,"content",None);role={"human":"user","ai":"assistant"}.get(msg_type,msg_type)
        if role in ("user","assistant") and content:plain.append({"role":role,"content":content})
    return plain
def load_history()->list[dict]:
    if not os.path.exists(SESSION_FILE):return []
    try:
        with open(SESSION_FILE) as f:return json.load(f)
    except (json.JSONDecodeError,OSError):return []
def save_history(messages:list)->None:
    Path(config.MEMORY_PATH).mkdir(parents=True,exist_ok=True)
    with open(SESSION_FILE,"w") as f:json.dump(_to_plain(messages),f,indent=2)
def maybe_summarize(messages:list)->list[dict]:
    plain=_to_plain(messages)
    if len(plain)<=MAX_MESSAGES_BEFORE_SUMMARY:return plain
    old,recent=plain[:-KEEP_RECENT_MESSAGES],plain[-KEEP_RECENT_MESSAGES:]; transcript="\n".join(f"{m['role']}: {m['content']}" for m in old)
    try:
        from agent.llm import get_llm
        response=get_llm().invoke("Summarize the key facts, decisions, and open threads from this conversation in 3-5 sentences, for use as background context later. Be concrete:\n\n"+transcript)
        summary_text=getattr(response,"content",str(response)).strip()
    except Exception:summary_text=f"(older conversation, {len(old)} messages, not summarized due to an error)"
    memory.remember_note(f"[past conversation summary] {summary_text}")
    return [{"role":"assistant","content":f"(Earlier in this conversation: {summary_text})"}]+recent
