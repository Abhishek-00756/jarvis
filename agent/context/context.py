"""Top-level current-context snapshot."""

from agent.computer.macos_control import get_frontmost_app
from agent.context.browser_context import get_active_browser_tab
from agent.context.clipboard import get_clipboard


def get_current_context() -> str:
    """Return current frontmost app, active browser tab (if supported), and clipboard."""
    frontmost = get_frontmost_app()
    lines = [f"Frontmost app: {frontmost}"]
    if frontmost in ("Safari", "Google Chrome"):
        lines.append(get_active_browser_tab())
    clipboard = get_clipboard()
    if clipboard:
        preview = clipboard[:300] + ("..." if len(clipboard) > 300 else "")
        lines.append(f"Clipboard: {preview}")
    else:
        lines.append("Clipboard: empty")
    return "\n".join(lines)
