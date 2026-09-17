"""WhatsApp Desktop automation: open a chat and start a call."""
import subprocess
CALL_BUTTON_CANDIDATES=["Voice call","Audio call","Start voice call","Call"]
VIDEO_BUTTON_CANDIDATES=["Video call","Start video call"]
def _run_applescript(script:str)->str:
    result=subprocess.run(["osascript","-e",script],capture_output=True,text=True,timeout=20)
    return result.stdout.strip() if result.returncode==0 else f"AppleScript error: {result.stderr.strip()}"
def dump_ui_tree(app_name:str="WhatsApp",max_depth:int=4)->str:
    script=f'''tell application "{app_name}" to activate
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
end tell'''
    return _run_applescript(script)
def open_chat(contact_name:str)->str:
    script=f'''tell application "WhatsApp" to activate
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
return "Opened search and selected top result for {contact_name}."'''
    return _run_applescript(script)
def _click_first_matching_button(candidates:list[str])->str|None:
    for label in candidates:
        script=f'''tell application "System Events"
 tell process "WhatsApp"
  try
   click (first button of window 1 whose description is "{label}")
   return "clicked:{label}"
  end try
 end tell
end tell
return "notfound"'''
        result=_run_applescript(script)
        if result.startswith("clicked:"): return label
    return None
def whatsapp_call(contact_name:str,video:bool=False)->str:
    opened=open_chat(contact_name)
    if "error" in opened.lower(): return f"Failed to open chat with {contact_name}: {opened}"
    candidates=VIDEO_BUTTON_CANDIDATES if video else CALL_BUTTON_CANDIDATES
    clicked=_click_first_matching_button(candidates); kind="video" if video else "voice"
    if clicked:return f"Opened chat with {contact_name} and clicked the '{clicked}' button to start a {kind} call."
    return f"Opened chat with {contact_name}, but couldn't find a {kind} call button under expected labels {candidates}. Run dump_ui_tree('WhatsApp') to calibrate."
def send_message(contact_name:str,message:str)->str:
    opened=open_chat(contact_name)
    if "error" in opened.lower(): return f"Failed to open chat with {contact_name}: {opened}"
    escaped=message.replace('"','\\"')
    script=f'''tell application "System Events"
 tell process "WhatsApp"
  delay 0.3
  keystroke "{escaped}"
  delay 0.2
  key code 36
 end tell
end tell
return "sent"'''
    result=_run_applescript(script)
    return f"Sent message to {contact_name}: {message}" if result=="sent" else f"Opened chat with {contact_name}, but sending the message failed: {result}"
