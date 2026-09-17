"""Reads the active tab from the user's REAL browser (Safari or Chrome),
via each browser's own AppleScript dictionary — not the agent's separate,
sandboxed Playwright browser.
"""

import subprocess
from agent.computer.macos_control import get_frontmost_app


def _run_applescript(script: str) -> str:
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return result.stdout.strip()


def get_active_browser_tab() -> str:
    """Return the URL and title of the active tab in the frontmost browser."""
    frontmost = get_frontmost_app()
    if frontmost == "Safari":
        script = '''
        tell application "Safari"
            set theURL to URL of front document
            set theTitle to name of front document
        end tell
        return theURL & "|||" & theTitle
        '''
    elif frontmost == "Google Chrome":
        script = '''
        tell application "Google Chrome"
            set theURL to URL of active tab of front window
            set theTitle to title of active tab of front window
        end tell
        return theURL & "|||" & theTitle
        '''
    else:
        return f"Frontmost app is '{frontmost}', not a supported browser (Safari or Google Chrome). Can't read an active tab from it."
    result = _run_applescript(script)
    if result.startswith("Error"):
        return result
    url, _, title = result.partition("|||")
    return f"Browser: {frontmost}\nURL: {url}\nTitle: {title}"
