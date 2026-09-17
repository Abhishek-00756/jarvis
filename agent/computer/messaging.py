"""Generalized messaging: native iMessage plus WhatsApp dispatcher."""
import subprocess

def _run_applescript(script:str)->str:
    result=subprocess.run(["osascript","-e",script],capture_output=True,text=True,timeout=15)
    return result.stdout.strip() if result.returncode==0 else f"Error: {result.stderr.strip()}"
def _escape(text:str)->str:return text.replace("\\","\\\\").replace('"','\\"')
def send_imessage(recipient:str,message:str)->str:
    script=f'''tell application "Messages"
        set targetBuddy to "{_escape(recipient)}"
        set targetService to id of 1st service whose service type = iMessage
        set theBuddy to buddy targetBuddy of service id targetService
        send "{_escape(message)}" to theBuddy
    end tell
    return "Sent."'''
    result=_run_applescript(script)
    return f"Sent iMessage to {recipient}." if result=="Sent." else f"Failed to send iMessage to {recipient}: {result}"
def send_message(platform:str,person:str,message:str)->str:
    platform=platform.lower().strip()
    if platform=="whatsapp":
        from agent.computer import whatsapp_control
        return whatsapp_control.send_message(person,message)
    if platform in ("imessage","messages","sms"):return send_imessage(person,message)
    return f"Unknown platform '{platform}'. Supported: whatsapp, imessage."
