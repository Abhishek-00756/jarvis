"""Long-term memory helpers."""
import os
from pathlib import Path
import json
from agent import config

FACTS_FILE = os.path.join(config.MEMORY_PATH, "facts.json")
NOTES_FILE = os.path.join(config.MEMORY_PATH, "notes.json")

def _load(path):
    try:
        with open(path) as f: return json.load(f)
    except (OSError, json.JSONDecodeError): return []

def _save(path, data):
    Path(config.MEMORY_PATH).mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f: json.dump(data, f, indent=2)

def remember_fact(key, value):
    facts = {x["key"]: x["value"] for x in _load(FACTS_FILE) if isinstance(x,dict) and "key" in x}
    facts[key] = value
    _save(FACTS_FILE, [{"key":k,"value":v} for k,v in facts.items()])
    return f"Remembered: {key} = {value}"

def recall_fact(key):
    for item in _load(FACTS_FILE):
        if item.get("key") == key: return str(item.get("value"))
    return "No fact found."

def add_note(note):
    notes = _load(NOTES_FILE)
    notes.append(note)
    _save(NOTES_FILE, notes)
    return "Note saved."

def recall_notes(query=""):
    notes = _load(NOTES_FILE)
    if not query: return "\n".join(map(str,notes[-20:])) or "No notes found."
    hits = [str(n) for n in notes if query.lower() in str(n).lower()]
    return "\n".join(hits[-20:]) or "No matching notes found."
