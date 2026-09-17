"""Central configuration for the agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.environ.get("JARVIS_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
TEMPERATURE = 0.2
MAX_ITERATIONS = 12
MEMORY_PATH = os.path.expanduser(os.environ.get("JARVIS_MEMORY_PATH", "~/.jarvis_agent/memory"))
Path(MEMORY_PATH).mkdir(parents=True, exist_ok=True)
CONFIRM_REQUIRED_TOOLS = {
    "run_shell_command", "write_file", "delete_file", "open_app", "type_text", "run_shortcut",
    "whatsapp_call", "whatsapp_send_message", "send_email", "add_calendar_event", "add_reminder",
    "add_note", "browser_navigate", "browser_click", "share_reel_to_instagram_dm", "lock_screen",
    "sleep_mac", "restart_mac", "shutdown_mac", "close_window", "move_file", "copy_file",
    "rename_file", "trash_file", "open_file", "extract_archive", "delete_reminder", "append_note",
    "send_imessage", "send_message", "quit_app", "click_menu_item", "browser_fill", "browser_download",
    "reply_email", "forward_email", "archive_email", "mark_email_read", "mark_email_unread",
    "browser_new_tab", "browser_close_tab", "browser_back", "browser_forward", "browser_reload",
    "browser_select", "browser_press_key", "ask_cloud_model",
}


def _get_secret_with_keychain_fallback(env_name: str) -> str:
    value = os.environ.get(env_name, "")
    if value:
        return value
    try:
        from agent.security.secrets import get_secret
        return get_secret(env_name) or ""
    except Exception:
        return ""

ANTHROPIC_API_KEY = _get_secret_with_keychain_fallback("ANTHROPIC_API_KEY")
CLOUD_FALLBACK_MODEL = os.environ.get("JARVIS_CLOUD_FALLBACK_MODEL", "claude-sonnet-5")
CLOUD_FALLBACK_ENABLED = bool(ANTHROPIC_API_KEY)
CLOUD_AUTO_ESCALATE = os.environ.get("JARVIS_CLOUD_AUTO_ESCALATE", "false").lower() == "true"
TAVILY_API_KEY = _get_secret_with_keychain_fallback("TAVILY_API_KEY")
WAKE_WORD = os.environ.get("JARVIS_WAKE_WORD", "hey_jarvis")
SAMPLE_RATE = 16000
STT_MODEL = "mlx-community/whisper-small-mlx"
TTS_VOICE = "af_heart"
DAEMON_LOG_PATH = os.path.expanduser("~/.jarvis_agent/daemon.log")
WATCHED_DIRECTORIES = []
