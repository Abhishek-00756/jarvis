"""Tool definitions for the Jarvis agent."""
import subprocess
from pathlib import Path
from langchain_core.tools import tool
from agent import config, memory
from agent.safety import confirm_action, requires_confirmation

@tool
def list_files(directory: str = ".") -> str:
    """List files and folders in a directory."""
    try:
        path=Path(directory).expanduser()
        return "\n".join(sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())) or "(empty directory)"
    except Exception as e: return f"Error listing directory: {e}"

@tool
def read_file(path: str) -> str:
    """Read a text file."""
    try: return Path(path).expanduser().read_text()[:8000]
    except Exception as e: return f"Error reading file: {e}"

@tool
def write_file(path: str, content: str) -> str:
    """Write a text file after confirmation."""
    if requires_confirmation("write_file") and not confirm_action("write_file", f"Write to {path}"): return "Action denied by user."
    try:
        p=Path(path).expanduser(); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content)
        return f"Wrote {len(content)} characters to {path}."
    except Exception as e: return f"Error writing file: {e}"

@tool
def delete_file(path: str) -> str:
    """Delete a file after confirmation."""
    if requires_confirmation("delete_file") and not confirm_action("delete_file", f"Delete {path}"): return "Action denied by user."
    try: Path(path).expanduser().unlink(); return f"Deleted {path}."
    except Exception as e: return f"Error deleting file: {e}"

@tool
def run_shell_command(command: str) -> str:
    """Run a shell command after confirmation."""
    if requires_confirmation("run_shell_command") and not confirm_action("run_shell_command", command): return "Action denied by user."
    try:
        r=subprocess.run(command,shell=True,capture_output=True,text=True,timeout=60)
        return (r.stdout+r.stderr)[-8000:] or "(no output)"
    except Exception as e: return f"Error running command: {e}"

@tool
def remember_fact(key: str, value: str) -> str: return memory.remember_fact(key,value)
@tool
def recall_fact(key: str) -> str: return memory.recall_fact(key)
@tool
def recall_notes(query: str = "") -> str: return memory.recall_notes(query)

@tool
def web_search_stub(query: str) -> str:
    """Use Tavily when configured; otherwise explain that search is unavailable."""
    if not config.TAVILY_API_KEY: return f"Web search unavailable without TAVILY_API_KEY. Query: {query}"
    try:
        from tavily import TavilyClient
        res=TavilyClient(config.TAVILY_API_KEY).search(query=query)
        return "\n".join(f"{x.get('title')}: {x.get('content','')}" for x in res.get("results",[])[:5])
    except Exception as e: return f"Web search error: {e}"

ALL_TOOLS=[list_files,read_file,write_file,delete_file,run_shell_command,remember_fact,recall_fact,recall_notes,web_search_stub]
