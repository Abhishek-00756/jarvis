"""macOS computer control, built on AppleScript + System Events.

This is the Accessibility-API approach (structured control via System
Events) rather than screenshot-based vision control — it's faster, cheaper
on tokens, and works with smaller local models. Every action here is gated
by agent/safety.py's confirmation check when called as a tool (see
agent/tools.py).

Requires: granting your terminal/VS Code Accessibility permission in
System Settings > Privacy & Security > Accessibility, and Automation
permission the first time each script runs.
"""

import subprocess


def _run_applescript(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        return f"AppleScript error: {result.stderr.strip()}"
    return result.stdout.strip()


def open_app(app_name: str) -> str:
    """Launch or focus an application by name."""
    script = f'tell application "{app_name}" to activate'
    output = _run_applescript(script)
    return output or f"Opened {app_name}."


def quit_app(app_name: str) -> str:
    """Quit an application by name."""
    script = f'tell application "{app_name}" to quit'
    output = _run_applescript(script)
    return output or f"Quit {app_name}."


def get_frontmost_app() -> str:
    """Return the name of the currently focused application."""
    script = (
        'tell application "System Events" to get name of first process '
        "whose frontmost is true"
    )
    return _run_applescript(script)


def list_open_windows() -> str:
    """List window titles of the frontmost application."""
    script = (
        'tell application "System Events"\n'
        "  set frontApp to first process whose frontmost is true\n"
        "  set windowTitles to name of every window of frontApp\n"
        "end tell\n"
        "return windowTitles"
    )
    return _run_applescript(script)


def type_text(text: str) -> str:
    """Type text into whatever UI element currently has focus."""
    escaped = text.replace('"', '\\"')
    script = f'tell application "System Events" to keystroke "{escaped}"'
    output = _run_applescript(script)
    return output or f"Typed {len(text)} characters."


def click_menu_item(app_name: str, menu_name: str, item_name: str) -> str:
    """Click a menu bar item."""
    script = (
        f'tell application "System Events"\n'
        f'  tell process "{app_name}"\n'
        f'    click menu item "{item_name}" of menu "{menu_name}" of menu bar 1\n'
        f"  end tell\n"
        f"end tell"
    )
    output = _run_applescript(script)
    return output or f"Clicked {menu_name} > {item_name} in {app_name}."


def run_shortcut(shortcut_name: str, input_text: str = "") -> str:
    """Run a macOS Shortcuts app shortcut by name, optionally with input text."""
    cmd = ["shortcuts", "run", shortcut_name]
    if input_text:
        result = subprocess.run(cmd, input=input_text, capture_output=True, text=True, timeout=30)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return (result.stdout + result.stderr).strip() or f"Ran shortcut: {shortcut_name}"
