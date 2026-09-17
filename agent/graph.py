"""LangGraph reasoning loop for Jarvis."""
from typing import Annotated, TypedDict
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from agent import config
from agent.llm import get_cloud_llm, get_llm
from agent.tools import ALL_TOOLS

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    iterations: int
    escalated: bool

SYSTEM_PROMPT = """You are a local, autonomous assistant running on the user's Mac. Use tools when they provide real information or take real action. Never claim an action happened unless a tool actually completed it. Prefer the least powerful tool that accomplishes the task. If a tool errors, inspect the error and try an alternate approach before reporting failure."""

def build_graph():
    llm = get_llm(bind_tools=ALL_TOOLS)
    def agent_node(state: AgentState):
        msgs = [{"role":"system","content":SYSTEM_PROMPT}] + state["messages"]
        response = llm.invoke(msgs)
        return {"messages": [response], "iterations": state.get("iterations",0)+1}
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))
    graph.set_entry_point("agent")
    def route(state):
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None) and state.get("iterations",0) < config.MAX_ITERATIONS:
            return "tools"
        return END
    graph.add_conditional_edges("agent", route, {"tools":"tools", END:END})
    graph.add_edge("tools", "agent")
    return graph.compile()
