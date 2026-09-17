"""Local web server for the chat UI.

Runs entirely on localhost — nothing is exposed to the network. The agent
logic is unchanged; this just gives it a browser front-end with an animated
status indicator instead of a bare terminal.
"""

import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent.graph import build_graph
from agent import session

app = FastAPI()
_agent = build_graph()
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class ChatRequest(BaseModel):
    history: list[dict]

class ChatResponse(BaseModel):
    reply: str
    history: list[dict]

@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/history")
def get_history():
    return {"history": session.load_history()}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = _agent.invoke({"messages": req.history, "iterations": 0})
    messages = result["messages"]
    final_message = messages[-1]
    reply = getattr(final_message, "content", str(final_message))
    plain_history = session.maybe_summarize(messages)
    session.save_history(plain_history)
    return ChatResponse(reply=reply, history=plain_history)

def run_web():
    import uvicorn
    print("Jarvis web UI running at http://127.0.0.1:8765")
    uvicorn.run(app, host="127.0.0.1", port=8765)
