"""Automation for Apple's own apps via AppleScript.

Unlike WhatsApp/Instagram, Apple's built-in apps have real, stable
AppleScript dictionaries — no Accessibility-tree guesswork, no fragile UI
selectors. These are the most reliable automations in the whole project.

Requires: Automation permission (macOS will prompt the first time each
app is scripted) in System Settings > Privacy & Security > Automation.
"""

import subprocess


def _run_applescript(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script], capture_output=True, text=True, timeout=20
    )
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return result.stdout.strip()


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


# --- Mail ---

def send_email(to: str, subject: str, body: str) -> str:
    """Compose and send an email via Mail.app."""
    script = f'''
    tell application "Mail"
        set newMsg to make new outgoing message with properties {{subject:"{_escape(subject)}", content:"{_escape(body)}", visible:false}}
        tell newMsg
            make new to recipient with properties {{address:"{_escape(to)}"}}
        end tell
        send newMsg
    end tell
    return "Email sent to {_escape(to)}."
    '''
    return _run_applescript(script)


def get_calendar_events_today() -> str:
    """List today's events across all calendars. Read-only."""
    script = '''
    tell application "Calendar"
        set theStartDate to current date
        set hours of theStartDate to 0
        set minutes of theStartDate to 0
        set seconds of theStartDate to 0
        set theEndDate to theStartDate + (1 * days)
        set eventList to {}
        repeat with cal in calendars
            try
                set theseEvents to (every event of cal whose start date ≥ theStartDate and start date < theEndDate)
                repeat with e in theseEvents
                    set end of eventList to (summary of e as string) & " at " & ((start date of e) as string)
                end repeat
            end try
        end repeat
        if (count of eventList) = 0 then
            return "No events today."
        end if
        return eventList
    end tell
    '''
    return _run_applescript(script)


def add_calendar_event(
    title: str, start_date_str: str, end_date_str: str, calendar_name: str = "Calendar"
) -> str:
    """Add a calendar event.

    Date format must be parseable by AppleScript's `date` coercion, e.g.
    "1/5/2026 3:00:00 PM" — always confirm the exact wording with the user
    before calling this, since a misparsed date silently creates the wrong
    event.
    """
    script = f'''
    tell application "Calendar"
        tell calendar "{_escape(calendar_name)}"
            make new event with properties {{summary:"{_escape(title)}", start date:date "{_escape(start_date_str)}", end date:date "{_escape(end_date_str)}"}}
        end tell
    end tell
    return "Added event '{_escape(title)}' to {_escape(calendar_name)}."
    '''
    return _run_applescript(script)


def add_reminder(text: str, list_name: str = "Reminders", due_date_str: str = "") -> str:
    """Add a reminder, optionally with a due date (AppleScript date format)."""
    due_clause = (
        f'set due date of newReminder to date "{_escape(due_date_str)}"'
        if due_date_str
        else ""
    )
    script = f'''
    tell application "Reminders"
        tell list "{_escape(list_name)}"
            set newReminder to make new reminder with properties {{name:"{_escape(text)}"}}
            {due_clause}
        end tell
    end tell
    return "Added reminder '{_escape(text)}' to {_escape(list_name)}."
    '''
    return _run_applescript(script)


def add_note(title: str, body: str) -> str:
    """Create a new note."""
    script = f'''
    tell application "Notes"
        make new note with properties {{name:"{_escape(title)}", body:"{_escape(title)}<br>{_escape(body)}"}}
    end tell
    return "Created note '{_escape(title)}'."
    '''
    return _run_applescript(script)
