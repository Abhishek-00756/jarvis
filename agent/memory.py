"""Long-term memory with facts and semantic notes."""
import json,os
from pathlib import Path
from agent import config
_FACTS_FILE=os.path.join(config.MEMORY_PATH,"facts.json")
_chroma_client=None; _collection=None
def _ensure_facts_file():
    Path(config.MEMORY_PATH).mkdir(parents=True,exist_ok=True)
    if not os.path.exists(_FACTS_FILE): open(_FACTS_FILE,"w").write("{}")
    return _FACTS_FILE
def get_all_facts()->dict:
    with open(_ensure_facts_file()) as f:return json.load(f)
def set_fact(key:str,value:str)->None:
    data=get_all_facts();data[key]=value
    with open(_ensure_facts_file(),"w") as f:json.dump(data,f,indent=2)
def get_fact(key:str)->str|None:return get_all_facts().get(key)
def _get_collection():
    global _chroma_client,_collection
    if _collection is not None:return _collection
    try:
        import chromadb
        _chroma_client=chromadb.PersistentClient(path=os.path.join(config.MEMORY_PATH,"chroma")); _collection=_chroma_client.get_or_create_collection("jarvis_notes"); return _collection
    except Exception:return None
_FALLBACK_NOTES_FILE=os.path.join(config.MEMORY_PATH,"notes_fallback.json")
def remember_note(note:str,note_id:str|None=None)->str:
    collection=_get_collection(); note_id=note_id or str(abs(hash(note)))
    if collection is not None: collection.add(documents=[note],ids=[note_id]); return f"Stored note ({note_id})."
    Path(config.MEMORY_PATH).mkdir(parents=True,exist_ok=True); notes=[]
    if os.path.exists(_FALLBACK_NOTES_FILE):
        with open(_FALLBACK_NOTES_FILE) as f:notes=json.load(f)
    notes.append({"id":note_id,"text":note})
    with open(_FALLBACK_NOTES_FILE,"w") as f:json.dump(notes,f,indent=2)
    return f"Stored note ({note_id}) [fallback keyword store — install chromadb for semantic recall]."
def recall_notes(query:str,top_k:int=3)->list[str]:
    collection=_get_collection()
    if collection is not None:
        results=collection.query(query_texts=[query],n_results=top_k); docs=results.get("documents",[[]]); return docs[0] if docs else []
    if not os.path.exists(_FALLBACK_NOTES_FILE):return []
    with open(_FALLBACK_NOTES_FILE) as f:notes=json.load(f)
    words=set(query.lower().split()); scored=[]
    for n in notes:
        overlap=len(words & set(n["text"].lower().split()))
        if overlap:scored.append((overlap,n["text"]))
    scored.sort(reverse=True);return [t for _,t in scored[:top_k]]
