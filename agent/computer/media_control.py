"""Media playback control via Music.app (AppleScript)."""
import subprocess
def _run_applescript(script:str)->str:
 result=subprocess.run(["osascript","-e",script],capture_output=True,text=True,timeout=10)
 return f"Error: {result.stderr.strip()}" if result.returncode!=0 else result.stdout.strip()
def play()->str:return _run_applescript('tell application "Music" to play') or "Playing."
def pause()->str:return _run_applescript('tell application "Music" to pause') or "Paused."
def next_track()->str:return _run_applescript('tell application "Music" to next track') or "Skipped to next track."
def previous_track()->str:return _run_applescript('tell application "Music" to previous track') or "Went to previous track."
def current_track()->str:
 script='''tell application "Music"
 if player state is playing then
  return (name of current track) & " by " & (artist of current track)
 else
  return "Nothing is currently playing."
 end if
end tell'''
 return _run_applescript(script)
