"""Central configuration for the agent.

All values can be overridden via environment variables (see .env.example).
"""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
MODEL_NAME=os.environ.get("JARVIS_MODEL","qwen2.5:7b")
OLLAMA_HOST=os.environ.get("OLLAMA_HOST","http://localhost:11434")
TEMPERATURE=0.2
MAX_ITERATIONS=12
MEMORY_PATH=os.path.expanduser(os.environ.get("JARVIS_MEMORY_PATH","~/.jarvis_agent/memory"))
Path(MEMORY_PATH).mkdir(parents=True,exist_ok=True)
CONFIRM_REQUIRED_TOOLS={"run_shell_command","write_file","delete_file","open_app","click_ui_element","type_text","run_shortcut","whatsapp_call","whatsapp_send_message","send_email","add_calendar_event","add_reminder","add_note","browser_navigate","browser_click","share_reel_to_instagram_dm"}
ANTHROPIC_API_KEY=os.environ.get("ANTHROPIC_API_KEY","")
CLOUD_FALLBACK_MODEL=os.environ.get("JARVIS_CLOUD_FALLBACK_MODEL","claude-sonnet-4-6")
CLOUD_FALLBACK_ENABLED=bool(ANTHROPIC_API_KEY)
TAVILY_API_KEY=os.environ.get("TAVILY_API_KEY","")
WAKE_WORD=os.environ.get("JARVIS_WAKE_WORD","hey_jarvis")
SAMPLE_RATE=16000
STT_MODEL="mlx-community/whisper-small-mlx"
TTS_VOICE="af_heart"
DAEMON_LOG_PATH=os.path.expanduser("~/.jarvis_agent/daemon.log")
WATCHED_DIRECTORIES=[]
