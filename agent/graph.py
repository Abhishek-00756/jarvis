"""The agent's reasoning loop, built as a LangGraph state graph."""

from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from agent import config
from agent.llm import get_cloud_llm, get_llm
from agent.tools import ALL_TOOLS, SAFE_CLOUD_TOOLS


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    iterations: int
    escalated: bool


SYSTEM_PROMPT = (
    "You are a local, autonomous assistant running on the user's Mac. You "
    "have tools for files, shell commands, web search, memory, macOS app/UI "
    "control, browser control, Apple app automation (Mail, Calendar, "
    "Reminders, Notes), and (if configured) escalating hard questions to a "
    "cloud model. Use tools when they'd give you real information or take a "
    "real action; answer directly when you already know the answer. Be "
    "concise. Never claim to have done something you did not actually do "
    "with a tool. Prefer the least powerful tool that accomplishes the task "
    "(e.g. read_file over run_shell_command). For known destinations like "
    "Instagram Reels/DMs, prefer browser_go_to over browser_click — it's "
    "far more reliable than clicking through a site's nav. When the user "
    "refers to \"this\" (page, reel, file, thing), call get_current_context "
    "FIRST — it checks the user's real, everyday browser (Safari/Chrome) "
    "and clipboard, which is usually what \"this\" actually refers to. Only "
    "fall back to the agent's own separate controlled browser "
    "(browser_get_current_url) if the user explicitly opened something "
    "through it earlier in this conversation. If neither has anything "
    "relevant, say so rather than guessing. If the user asks to send a "
    "reel/post \"on Instagram\" or \"within Instagram\", use "
    "share_reel_to_instagram_dm (native Instagram sharing) — this requires "
    "the reel to be open in the agent's controlled browser, so navigate "
    "there first if needed. If they ask to send it \"on WhatsApp\" or don't "
    "specify a platform, get the relevant URL (get_current_context or "
    "browser_get_current_url, whichever has it) and use "
    "whatsapp_send_message instead.\n\n"
    "SELF-CORRECTION: if a tool call fails or returns an error, do not just "
    "report the failure and stop. Read the error, try an alternate approach "
    "(a different tool, a corrected argument, or a diagnostic tool like "
    "inspect_app_ui), and retry before giving up. Only report failure to "
    "the user after a genuine attempt to recover has also failed — and when "
    "you do, say plainly what you tried and what didn't work."
)


def agent_node(state: AgentState) -> dict:
    use_cloud = state.get("escalated", False) and config.CLOUD_FALLBACK_ENABLED
    if use_cloud:
        llm = get_cloud_llm(bind_tools=SAFE_CLOUD_TOOLS)
    else:
        llm = get_llm(bind_tools=ALL_TOOLS)
    messages = state["messages"]
    if not messages or messages[0].type != "system":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(messages)
    response = llm.invoke(messages)
    return {"messages": [response], "iterations": state.get("iterations", 0) + 1}


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    if state.get("iterations", 0) >= config.MAX_ITERATIONS and not state.get("escalated", False):
        if config.CLOUD_FALLBACK_ENABLED and config.CLOUD_AUTO_ESCALATE:
            return "escalate"
        return "end"
    return "end"


def escalate_node(state: AgentState) -> dict:
    print("[graph] Local model did not resolve in time — escalating to cloud model.")
    return {"escalated": True, "iterations": 0}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))
    graph.add_node("escalate", escalate_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "escalate": "escalate", "end": END},
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("escalate", "agent")
    return graph.compile()
