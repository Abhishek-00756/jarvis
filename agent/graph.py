"""The agent's reasoning loop, built as a LangGraph state graph."""
from typing import Annotated,TypedDict
from langgraph.graph import END,StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from agent import config
from agent.llm import get_cloud_llm,get_llm
from agent.tools import ALL_TOOLS
class AgentState(TypedDict):
    messages: Annotated[list,add_messages]
    iterations:int
    escalated:bool
SYSTEM_PROMPT=("You are a local, autonomous assistant running on the user's Mac. You have tools for files, shell commands, web search, memory, macOS app/UI control, browser control, Apple app automation (Mail, Calendar, Reminders, Notes), and (if configured) escalating hard questions to a cloud model. Use tools when they'd give you real information or take a real action; answer directly when you already know the answer. Be concise. Never claim to have done something you did not actually do with a tool. Prefer the least powerful tool that accomplishes the task. For known destinations like Instagram Reels/DMs, prefer browser_go_to over browser_click. When the user refers to this page/reel/video, use browser_get_current_url before acting. If the user asks to send a reel on Instagram, use share_reel_to_instagram_dm. If they ask to send it on WhatsApp or don't specify a platform, use browser_get_current_url and whatsapp_send_message.\n\nSELF-CORRECTION: if a tool call fails or returns an error, read the error, try an alternate approach or diagnostic tool, and retry before giving up.")
def agent_node(state:AgentState)->dict:
    use_cloud=state.get("escalated",False) and config.CLOUD_FALLBACK_ENABLED
    llm=(get_cloud_llm if use_cloud else get_llm)(bind_tools=ALL_TOOLS)
    messages=state["messages"]
    if not messages or messages[0].type!="system": messages=[{"role":"system","content":SYSTEM_PROMPT}]+list(messages)
    response=llm.invoke(messages)
    return {"messages":[response],"iterations":state.get("iterations",0)+1}
def should_continue(state:AgentState)->str:
    last=state["messages"][-1]
    if getattr(last,"tool_calls",None): return "tools"
    if state.get("iterations",0)>=config.MAX_ITERATIONS and not state.get("escalated",False):
        return "escalate" if config.CLOUD_FALLBACK_ENABLED else "end"
    return "end"
def escalate_node(state:AgentState)->dict:
    print("[graph] Local model did not resolve in time — escalating to cloud model.")
    return {"escalated":True,"iterations":0}
def build_graph():
    graph=StateGraph(AgentState); graph.add_node("agent",agent_node); graph.add_node("tools",ToolNode(ALL_TOOLS)); graph.add_node("escalate",escalate_node); graph.set_entry_point("agent")
    graph.add_conditional_edges("agent",should_continue,{"tools":"tools","escalate":"escalate","end":END}); graph.add_edge("tools","agent"); graph.add_edge("escalate","agent")
    return graph.compile()
