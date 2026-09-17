"""Local FastAPI web UI for Jarvis."""
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent.graph import build_graph
from agent import session
app=FastAPI(); _agent=build_graph()
STATIC_DIR=os.path.join(os.path.dirname(__file__),'static')
app.mount('/static',StaticFiles(directory=STATIC_DIR),name='static')
class ChatRequest(BaseModel): history:list[dict]
class ChatResponse(BaseModel): reply:str; history:list[dict]
@app.get('/')
def index(): return FileResponse(os.path.join(STATIC_DIR,'index.html'))
@app.get('/history')
def get_history(): return {'history':session.load_history()}
@app.post('/chat',response_model=ChatResponse)
def chat(req:ChatRequest):
    result=_agent.invoke({'messages':req.history,'iterations':0}); messages=result['messages']; reply=getattr(messages[-1],'content',str(messages[-1])); plain=session.maybe_summarize(messages); session.save_history(plain); return ChatResponse(reply=reply,history=plain)
def run_web():
    import uvicorn
    print('Jarvis web UI running at http://127.0.0.1:8765')
    uvicorn.run(app,host='127.0.0.1',port=8765)
