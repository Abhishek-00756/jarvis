"""Example MCP server exposing the filesystem tools as a standalone process.

This demonstrates the migration path mentioned in the README: instead of
importing tools.py directly in-process, you can run tools behind an MCP
server and have the agent (or any other MCP-compatible client — Claude
Desktop, Claude Code, etc.) connect to it over stdio.

Run standalone with:
    python -m agent.mcp_servers.filesystem_server

Then point an MCP client's config at this command. This one file is a
template — copy the pattern for browser_server.py, macos_control_server.py,
etc. as you split more tools out.
"""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("jarvis-filesystem")


@mcp.tool()
def list_files(directory: str = ".") -> str:
    """List files and folders in the given directory."""
    try:
        path = Path(directory).expanduser()
        entries = sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())
        return "\n".join(entries) if entries else "(empty directory)"
    except Exception as e:
        return f"Error listing directory: {e}"


@mcp.tool()
def read_file(path: str) -> str:
    """Read and return the text content of a file."""
    try:
        return Path(path).expanduser().read_text()[:8000]
    except Exception as e:
        return f"Error reading file: {e}"


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write text content to a file, creating it if needed.

    Note: this server-side tool has no interactive confirmation prompt
    (MCP servers run headless). If you expose this to other clients,
    add your own approval step in the calling client, or restrict the
    server to a safe working directory.
    """
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Wrote {len(content)} characters to {path}."
    except Exception as e:
        return f"Error writing file: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
