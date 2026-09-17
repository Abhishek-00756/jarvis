"""WhatsApp Desktop automation: open a chat and start a call.

Honest caveat up front: WhatsApp Desktop is an Electron/Catalyst app with no
AppleScript dictionary, so this works by driving the Accessibility (UI)
tree through System Events — the same technique real Mac "computer use"
agents use. That means it's more fragile than a proper API call: exact
button labels can differ between WhatsApp versions/locales, so this ships
with a small set of label candidates AND a diagnostic function
(`dump_ui_tree`) to find the real ones on your installed version if the
defaults don't match.

Calibration workflow if a call doesn't trigger:
    1. Open WhatsApp, open any chat with a call button visible.
    2. Run `dump_ui_tree("WhatsApp")` (exposed as a tool) and read the
       output for the call/video button's actual "description" or "name".
    3. Add that exact string to CALL_BUTTON_CANDIDATES / VIDEO_BUTTON_CANDIDATES
       below.

Requires: Accessibility permission granted to your terminal/VS Code in
System Settings > Privacy & Security > Accessibility.
"""

import subprocess

CALL_BUTTON_CANDIDATES = ["Voice call", "Audio call", "Start voice call", "Call"]
VIDEO_BUTTON_CANDIDATES = ["Video call", "Start video call"]


def _run_applescript(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script], capture_output=True, text=True, timeout=20
    )
    if result.returncode != 0:
        return f"AppleScript error: {result.stderr.strip()}"
    return result.stdout.strip()


def dump_ui_tree(app_name: str = "WhatsApp", max_depth: int = 4) -> str:
    """Dump the Accessibility UI element tree of an app's frontmost window."""
    script = f'''
    tell application "{app_name}" to activate
    delay 0.5
    tell application "System Events"
        tell process "{app_name}"
            set outputList to {{}}
            set win to window 1
            set elementList to entire contents of win
            repeat with elem in elementList
                try
                    set elemDesc to (role of elem as string) & " | name: " & (name of elem as string)
                    set end of outputList to elemDesc
                end try
            end repeat
            return outputList
        end tell
    end tell
    '''
    return _run_applescript(script)


def open_chat(contact_name: str) -> str:
    """Open a chat with the given contact via WhatsApp's search (Cmd+F)."""
    script = f'''
    tell application "WhatsApp" to activate
    delay 1
    tell application "System Events"
        tell process "WhatsApp"
            keystroke "f" using command down
            delay 0.5
            keystroke "{contact_name}"
            delay 1
            key code 36
            delay 1
        end tell
    end tell
    return "Opened search and selected top result for {contact_name}."
    '''
    return _run_applescript(script)


def _click_first_matching_button(candidates: list[str]) -> str | None:
    for label in candidates:
        script = f'''
        tell application "System Events"
            tell process "WhatsApp"
                try
                    click (first button of window 1 whose description is "{label}")
                    return "clicked:{label}"
                end try
            end tell
        end tell
        return "notfound"
        '''
        result = _run_applescript(script)
        if result.startswith("clicked:"):
            return label
    return None


def whatsapp_call(contact_name: str, video: bool = False) -> str:
    """Open a chat and attempt to start a voice/video call."""
    open_result = open_chat(contact_name)
    if "error" in open_result.lower():
        return f"Failed to open chat with {contact_name}: {open_result}"
    candidates = VIDEO_BUTTON_CANDIDATES if video else CALL_BUTTON_CANDIDATES
    clicked_label = _click_first_matching_button(candidates)
    call_kind = "video" if video else "voice"
    if clicked_label:
        return f"Opened chat with {contact_name} and clicked the '{clicked_label}' button to start a {call_kind} call."
    return (
        f"Opened chat with {contact_name}, but couldn't find a {call_kind} call "
        f"button under any of the expected labels {candidates}. Run "
        f"dump_ui_tree('WhatsApp') to find the actual button label on your "
        f"WhatsApp version, then add it to the candidates list in "
        f"agent/computer/whatsapp_control.py."
    )


def send_message(contact_name: str, message: str) -> str:
    """Open a chat with `contact_name` and send a text message or link."""
    open_result = open_chat(contact_name)
    if "error" in open_result.lower():
        return f"Failed to open chat with {contact_name}: {open_result}"
    escaped = message.replace('"', '\\"')
    script = f'''
    tell application "System Events"
        tell process "WhatsApp"
            delay 0.3
            keystroke "{escaped}"
            delay 0.2
            key code 36
        end tell
    end tell
    return "sent"
    '''
    result = _run_applescript(script)
    if result == "sent":
        return f"Sent message to {contact_name}: {message}"
    return f"Opened chat with {contact_name}, but sending the message failed: {result}"
