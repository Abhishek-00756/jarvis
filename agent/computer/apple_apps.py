"""Automation for Apple's own apps via AppleScript."""
import subprocess

def _run_applescript(script:str)->str:
    result=subprocess.run(["osascript","-e",script],capture_output=True,text=True,timeout=20)
    return result.stdout.strip() if result.returncode==0 else f"Error: {result.stderr.strip()}"
def _escape(text:str)->str:return text.replace("\\","\\\\").replace('"','\\"')

def send_email(to:str,subject:str,body:str)->str:
    script=f'''tell application "Mail"
        set newMsg to make new outgoing message with properties {{subject:"{_escape(subject)}", content:"{_escape(body)}", visible:false}}
        tell newMsg
            make new to recipient with properties {{address:"{_escape(to)}"}}
        end tell
        send newMsg
    end tell
    return "Email sent to {_escape(to)}."'''
    return _run_applescript(script)

def get_calendar_events_today()->str:
    script='''tell application "Calendar"
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
        if (count of eventList) = 0 then return "No events today."
        return eventList
    end tell'''
    return _run_applescript(script)

def add_calendar_event(title:str,start_date_str:str,end_date_str:str,calendar_name:str="Calendar")->str:
    script=f'''tell application "Calendar"
        tell calendar "{_escape(calendar_name)}"
            make new event with properties {{summary:"{_escape(title)}", start date:date "{_escape(start_date_str)}", end date:date "{_escape(end_date_str)}"}}
        end tell
    end tell
    return "Added event '{_escape(title)}' to {_escape(calendar_name)}."'''
    return _run_applescript(script)

def add_reminder(text:str,list_name:str="Reminders",due_date_str:str="")->str:
    due_clause=f'set due date of newReminder to date "{_escape(due_date_str)}"' if due_date_str else ""
    script=f'''tell application "Reminders"
        tell list "{_escape(list_name)}"
            set newReminder to make new reminder with properties {{name:"{_escape(text)}"}}
            {due_clause}
        end tell
    end tell
    return "Added reminder '{_escape(text)}' to {_escape(list_name)}."'''
    return _run_applescript(script)

def add_note(title:str,body:str)->str:
    script=f'''tell application "Notes"
        make new note with properties {{name:"{_escape(title)}", body:"{_escape(title)}<br>{_escape(body)}"}}
    end tell
    return "Created note '{_escape(title)}'."'''
    return _run_applescript(script)

def get_calendar_events_range(days_ahead:int=7)->str:
    script=f'''tell application "Calendar"
        set theStartDate to current date
        set hours of theStartDate to 0
        set minutes of theStartDate to 0
        set seconds of theStartDate to 0
        set theEndDate to theStartDate + ({days_ahead} * days)
        set eventList to {{}}
        repeat with cal in calendars
            try
                set theseEvents to (every event of cal whose start date ≥ theStartDate and start date < theEndDate)
                repeat with e in theseEvents
                    set end of eventList to (summary of e as string) & " at " & ((start date of e) as string)
                end repeat
            end try
        end repeat
        if (count of eventList) = 0 then return "No events in range."
        return eventList
    end tell'''
    return _run_applescript(script)

def find_event(query:str)->str:
    script=f'''tell application "Calendar"
        set q to "{_escape(query)}"
        set matches to {{}}
        repeat with cal in calendars
            try
                set evs to every event of cal whose summary contains q
                repeat with e in evs
                    set end of matches to (summary of e as string) & " at " & ((start date of e) as string)
                end repeat
            end try
        end repeat
        if (count of matches) = 0 then return "No matching events."
        return matches
    end tell'''
    return _run_applescript(script)

def list_reminders(list_name:str="")->str:
    target=f'list "{_escape(list_name)}"' if list_name else 'lists'
    script=f'''tell application "Reminders"
        set out to {{}}
        repeat with lst in {target}
            try
                repeat with r in reminders of lst whose completed is false
                    set end of out to (name of r as string)
                end repeat
            end try
        end repeat
        if (count of out) = 0 then return "No open reminders."
        return out
    end tell'''
    return _run_applescript(script)

def complete_reminder(query:str)->str:
    script=f'''tell application "Reminders"
        repeat with lst in lists
            try
                set rs to every reminder of lst whose completed is false and name contains "{_escape(query)}"
                if (count of rs) > 0 then
                    set completed of item 1 of rs to true
                    return "Completed reminder: " & (name of item 1 of rs as string)
                end if
            end try
        end repeat
        return "No matching reminder."
    end tell'''
    return _run_applescript(script)

def delete_reminder(query:str)->str:
    script=f'''tell application "Reminders"
        repeat with lst in lists
            try
                set rs to every reminder of lst whose name contains "{_escape(query)}"
                if (count of rs) > 0 then
                    delete item 1 of rs
                    return "Deleted reminder."
                end if
            end try
        end repeat
        return "No matching reminder."
    end tell'''
    return _run_applescript(script)

def search_notes(query:str)->str:
    script=f'''tell application "Notes"
        set q to "{_escape(query)}"
        set out to {{}}
        repeat with n in notes
            try
                if (name of n as string) contains q or (body of n as string) contains q then set end of out to name of n as string
            end try
        end repeat
        if (count of out) = 0 then return "No matching notes."
        return out
    end tell'''
    return _run_applescript(script)

def read_note(title:str)->str:
    script=f'''tell application "Notes"
        repeat with n in notes
            try
                if (name of n as string) is "{_escape(title)}" then return body of n as string
            end try
        end repeat
        return "Note not found."
    end tell'''
    return _run_applescript(script)

def append_note(title:str,text:str)->str:
    script=f'''tell application "Notes"
        repeat with n in notes
            try
                if (name of n as string) is "{_escape(title)}" then
                    set body of n to (body of n as string) & "<br>" & "{_escape(text)}"
                    return "Appended to note."
                end if
            end try
        end repeat
        return "Note not found."
    end tell'''
    return _run_applescript(script)

def get_unread_emails()->str:
    script='''tell application "Mail"
        set out to {}
        repeat with a in accounts
            try
                repeat with m in messages of inbox of a whose read status is false
                    set end of out to ((subject of m as string) & " — " & (sender of m as string))
                end repeat
            end try
        end repeat
        if (count of out) = 0 then return "No unread email."
        return out
    end tell'''
    return _run_applescript(script)

def search_emails(query:str)->str:
    script=f'''tell application "Mail"
        set q to "{_escape(query)}"
        set out to {{}}
        repeat with a in accounts
            try
                repeat with m in messages of inbox whose subject contains q or sender contains q
                    set end of out to ((subject of m as string) & " — " & (sender of m as string))
                end repeat
            end try
        end repeat
        if (count of out) = 0 then return "No matching emails."
        return out
    end tell'''
    return _run_applescript(script)

def search_contact(query:str)->str:
    script=f'''tell application "Contacts"
        set q to "{_escape(query)}"
        set out to {{}}
        repeat with p in people
            try
                if (name of p as string) contains q then set end of out to (name of p as string)
            end try
        end repeat
        if (count of out) = 0 then return "No matching contacts."
        return out
    end tell'''
    return _run_applescript(script)
