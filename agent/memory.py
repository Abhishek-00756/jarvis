"""Long-term memory.

Two tiers:
  - Flat facts (key/value) for simple preferences — always available.
  - Semantic memory (Chroma vector store) for free-text notes the agent
    can recall by meaning, not just by exact key. Falls back gracefully
    to keyword search if chromadb isn't installed/initialized yet, so the
    agent still works before you finish Phase 4 setup.
"""

import json
import os
from pathlib import Path

from agent import config
from agent.util import atomic_write_json

_FACTS_FILE = os.path.join(config.MEMORY_PATH, "facts.json")

_chroma_client = None
_collection = None


def _ensure_facts_file():
    Path(config.MEMORY_PATH).mkdir(parents=True, exist_ok=True)
    if not os.path.exists(_FACTS_FILE):
        with open(_FACTS_FILE, "w") as f:
            json.dump({}, f)
    return _FACTS_FILE


def get_all_facts() -> dict:
    path = _ensure_facts_file()
    with open(path) as f:
        return json.load(f)


def set_fact(key: str, value: str) -> None:
    path = _ensure_facts_file()
    data = get_all_facts()
    data[key] = value
    atomic_write_json(path, data)


def get_fact(key: str) -> str | None:
    return get_all_facts().get(key)


def _get_collection():
    global _chroma_client, _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        _chroma_client = chromadb.PersistentClient(
            path=os.path.join(config.MEMORY_PATH, "chroma")
        )
        _collection = _chroma_client.get_or_create_collection("jarvis_notes")
        return _collection
    except Exception:
        return None


_FALLBACK_NOTES_FILE = os.path.join(config.MEMORY_PATH, "notes_fallback.json")


def remember_note(note: str, note_id: str | None = None) -> str:
    """Store a free-text note for later semantic recall."""
    import uuid
    collection = _get_collection()
    note_id = note_id or str(uuid.uuid4())[:12]
    if collection is not None:
        collection.add(documents=[note], ids=[note_id])
        return f"Stored note ({note_id})."
    Path(config.MEMORY_PATH).mkdir(parents=True, exist_ok=True)
    notes = []
    if os.path.exists(_FALLBACK_NOTES_FILE):
        with open(_FALLBACK_NOTES_FILE) as f:
            notes = json.load(f)
    notes.append({"id": note_id, "text": note})
    atomic_write_json(_FALLBACK_NOTES_FILE, notes)
    return f"Stored note ({note_id}) [fallback keyword store — install chromadb for semantic recall]."


def recall_notes(query: str, top_k: int = 3) -> list[str]:
    """Return the most relevant notes for a query."""
    collection = _get_collection()
    if collection is not None:
        results = collection.query(query_texts=[query], n_results=top_k)
        docs = results.get("documents", [[]])
        return docs[0] if docs else []
    if not os.path.exists(_FALLBACK_NOTES_FILE):
        return []
    with open(_FALLBACK_NOTES_FILE) as f:
        notes = json.load(f)
    query_words = set(query.lower().split())
    scored = []
    for n in notes:
        overlap = len(query_words & set(n["text"].lower().split()))
        if overlap:
            scored.append((overlap, n["text"]))
    scored.sort(reverse=True)
    return [text for _, text in scored[:top_k]]
