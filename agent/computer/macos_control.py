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
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        return f"AppleScript error: {result.stderr.strip()}"
    return result.stdout.strip()


def open_app(app_name: str) -> str:
    output = _run_applescript(f'tell application "{app_name}" to activate')
    return output or f"Opened {app_name}."


def quit_app(app_name: str) -> str:
    output = _run_applescript(f'tell application "{app_name}" to quit')
    return output or f"Quit {app_name}."


def get_frontmost_app() -> str:
    return _run_applescript('tell application "System Events" to get name of first process whose frontmost is true')


def list_open_windows() -> str:
    script=('tell application "System Events"\nset frontApp to first process whose frontmost is true\nset windowTitles to name of every window of frontApp\nend tell\nreturn windowTitles')
    return _run_applescript(script)


def type_text(text: str) -> str:
    escaped=text.replace('"','\\"')
    output=_run_applescript(f'tell application "System Events" to keystroke "{escaped}"')
    return output or f"Typed {len(text)} characters."


def click_menu_item(app_name: str, menu_name: str, item_name: str) -> str:
    script=(f'tell application "System Events"\n  tell process "{app_name}"\n    click menu item "{item_name}" of menu "{menu_name}" of menu bar 1\n  end tell\nend tell')
    return _run_applescript(script) or f"Clicked {menu_name} > {item_name} in {app_name}."


def run_shortcut(shortcut_name: str, input_text: str = "") -> str:
    cmd=["shortcuts","run",shortcut_name]
    result=subprocess.run(cmd,input=input_text if input_text else None,capture_output=True,text=True,timeout=30)
    return (result.stdout+result.stderr).strip() or f"Ran shortcut: {shortcut_name}"


def close_window(app_name: str) -> str:
    script=f'tell application "System Events" to tell process "{app_name}" to click button 1 of (first window whose subrole is "AXStandardWindow")'
    return _run_applescript(script) or f"Closed frontmost window of {app_name}."


def minimize_window(app_name: str) -> str:
    script=f'tell application "System Events" to tell process "{app_name}" to set value of attribute "AXMinimized" of window 1 to true'
    return _run_applescript(script) or f"Minimized {app_name}."


def maximize_window(app_name: str) -> str:
    script=f'tell application "System Events" to tell process "{app_name}" to click button 2 of window 1'
    return _run_applescript(script) or f"Maximized {app_name}."


def move_window(app_name: str,x:int,y:int)->str:
    script=f'tell application "System Events" to tell process "{app_name}" to set position of window 1 to {{{x}, {y}}}'
    return _run_applescript(script) or f"Moved {app_name} window to ({x}, {y})."


def resize_window(app_name: str,width:int,height:int)->str:
    script=f'tell application "System Events" to tell process "{app_name}" to set size of window 1 to {{{width}, {height}}}'
    return _run_applescript(script) or f"Resized {app_name} window to {width}x{height}."
