"""Permission gate for impactful actions, plus a structured audit log."""

import subprocess
from agent import config
from agent.security.audit import log_action


def requires_confirmation(tool_name: str) -> bool:
    return tool_name in config.CONFIRM_REQUIRED_TOOLS


def confirm_action(tool_name: str, description: str) -> bool:
    approved = _native_dialog(tool_name, description)
    log_action(tool_name, description, approved)
    return approved


def _native_dialog(tool_name: str, description: str) -> bool:
    escaped = description.replace('"', '\\"')
    script = f'''display dialog "Jarvis wants to: {escaped}" with title "Approval needed — {tool_name}" buttons {{"Deny", "Allow"}} default button "Allow"'''
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=60
        )
        return "Allow" in result.stdout
    except Exception:
        return _terminal_fallback(tool_name, description)


def _terminal_fallback(tool_name: str, description: str) -> bool:
    print(f"\n[CONFIRM NEEDED] Tool: {tool_name}")
    print(f"  Action: {description}")
    answer = input("  Allow this action? [y/N]: ").strip().lower()
    return answer == "y"
