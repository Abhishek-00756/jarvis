"""Lightweight dynamic tool discovery for Jarvis.

V1 deliberately uses deterministic keyword/category matching instead of a
separate model. A request gets a small relevant tool subset; ambiguous
requests fall back to the complete interactive surface rather than guessing.
"""

from agent import config, tools as tools_module
from agent.extended_tools import EXTRA_TOOLS

ALL_INTERACTIVE_TOOLS = [*tools_module.ALL_TOOLS, *EXTRA_TOOLS]
_TOOLS_BY_NAME = {t.name: t for t in ALL_INTERACTIVE_TOOLS}

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "filesystem": ["file", "files", "folder", "directory", "document", "pdf", "docx", "pptx", "spreadsheet", "csv", "download", "trash", "rename", "move", "copy", "compress", "zip", "extract", "unzip"],
    "browser": ["browser", "website", "webpage", "web page", "url", "tab", "instagram", "reel", "chrome", "safari", "link", "scroll", "download"],
    "messaging": ["whatsapp", "imessage", "text message", "send a message", "message", "call him", "call her", "call them", "dm", "direct message"],
    "email": ["email", "mail", "inbox", "unread", "reply", "forward", "draft"],
    "calendar_reminders_notes": ["calendar", "event", "meeting", "schedule", "reminder", "remind me", "note", "notes"],
    "contacts": ["contact", "phone number"],
    "media": ["music", "song", "play", "pause music", "skip track", "next track", "previous track"],
    "system": ["battery", "wifi", "wi-fi", "network", "disk space", "cpu", "memory usage", "volume", "brightness", "lock my screen", "sleep", "restart", "shut down", "shutdown", "uptime", "what time"],
    "windows_apps": ["window", "open app", "close app", "quit", "minimize", "maximize", "resize", "menu bar", "shortcut"],
    "screen": ["screen", "ocr", "what does this say", "error on my screen", "read my screen"],
    "context": ["this page", "this reel", "this file", "this post", "clipboard", "copied", "current tab", "what am i looking at", "on my screen"],
    "memory_tasks": ["remember", "recall", "memory", "task", "todo", "to-do", "what am i working on"],
    "shell": ["shell", "terminal command", "run a command"],
    "web_search": ["search the web", "google", "look up online", "search for", "web search"],
    "cloud": ["ask claude", "use the cloud", "harder question"],
}

CATEGORY_TOOL_NAMES: dict[str, list[str]] = {
    "filesystem": ["list_files", "read_file", "write_file", "delete_file", "find_file", "search_file_content", "get_recent_files", "get_file_info", "move_file", "copy_file", "rename_file", "create_folder", "trash_file", "reveal_in_finder", "open_file", "compress_file", "extract_archive", "read_pdf", "search_pdf", "read_docx", "read_pptx", "read_spreadsheet"],
    "browser": ["browser_navigate", "browser_go_to", "browser_get_text", "browser_get_current_url", "browser_click", "browser_fill", "browser_select", "browser_scroll", "browser_press_key", "browser_get_links", "browser_download", "browser_new_tab", "browser_list_tabs", "browser_switch_tab", "browser_close_tab", "browser_back", "browser_forward", "browser_reload", "browser_close", "browser_inspect_page", "share_reel_to_instagram_dm"],
    "messaging": ["whatsapp_call", "whatsapp_send_message", "send_imessage", "send_message", "inspect_app_ui"],
    "email": ["send_email", "get_unread_emails", "search_emails", "draft_email", "reply_email", "forward_email", "mark_email_read", "mark_email_unread", "archive_email"],
    "calendar_reminders_notes": ["get_calendar_events_today", "get_calendar_events_range", "find_event", "add_calendar_event", "list_reminders", "add_reminder", "complete_reminder", "delete_reminder", "search_notes", "read_note", "append_note", "add_note"],
    "contacts": ["search_contact"],
    "media": ["media_play", "media_pause", "media_next_track", "media_previous_track", "media_current_track"],
    "system": ["get_battery_status", "get_disk_usage", "get_network_status", "get_volume_level", "set_volume_level", "mute_system_volume", "unmute_system_volume", "set_screen_brightness", "lock_screen", "sleep_mac", "restart_mac", "shutdown_mac", "get_cpu_usage", "get_memory_usage", "get_uptime", "get_current_time_and_timezone"],
    "windows_apps": ["open_app", "get_frontmost_app", "type_text", "run_shortcut", "quit_app", "click_menu_item", "list_open_windows", "close_window", "minimize_window", "maximize_window", "move_window", "resize_window"],
    "screen": ["read_screen_text", "find_text_on_screen", "get_screen_context"],
    "context": ["get_current_context", "get_active_browser_tab", "get_clipboard", "set_clipboard"],
    "memory_tasks": ["remember_fact", "recall_fact", "remember_note", "recall_notes", "create_task", "list_tasks", "complete_task", "delete_task", "what_did_you_do_today"],
    "shell": ["run_shell_command"],
    "web_search": ["web_search"],
    "cloud": ["ask_cloud_model"],
}


def _required_tools_for_request(lower: str) -> list[str]:
    """Keep cross-domain dependencies from being dropped by the tool cap."""
    required: list[str] = []
    if any(kw in lower for kw in CATEGORY_KEYWORDS["context"]):
        required.append("get_current_context")
        if any(token in lower for token in ("tab", "reel", "page")):
            required.append("get_active_browser_tab")
    if "whatsapp" in lower:
        required.append("whatsapp_send_message")
    elif "imessage" in lower:
        required.append("send_imessage")
    elif any(kw in lower for kw in ("send a message", "message", "dm", "direct message")):
        required.append("send_message")
    if any(kw in lower for kw in ("reel", "instagram")):
        required.extend(["browser_get_current_url", "browser_go_to", "browser_get_text"])
    elif any(kw in lower for kw in ("browser", "webpage", "web page")):
        required.extend(["browser_get_current_url", "browser_get_text"])
    return list(dict.fromkeys(required))


def _category_scores(user_message: str) -> dict[str, int]:
    lower = user_message.lower()
    return {category: sum(1 for keyword in keywords if keyword in lower) for category, keywords in CATEGORY_KEYWORDS.items()}


def select_relevant_tools(user_message: str, max_tools: int = 25, all_tools: list | None = None) -> list:
    """Return relevant tools; use the full registry when routing is uncertain."""
    available = list(all_tools if all_tools is not None else ALL_INTERACTIVE_TOOLS)
    if not config.DYNAMIC_TOOL_SELECTION or not user_message:
        return available
    scores = _category_scores(user_message)
    matched = [category for category, _score in sorted(scores.items(), key=lambda item: (-item[1], item[0])) if scores[category] > 0]
    if not matched:
        return available

    selected_names: list[str] = []
    for name in _required_tools_for_request(user_message.lower()):
        if name in _TOOLS_BY_NAME and name not in selected_names:
            selected_names.append(name)

    for category in matched:
        for name in CATEGORY_TOOL_NAMES.get(category, []):
            if name in _TOOLS_BY_NAME and name not in selected_names:
                selected_names.append(name)
            if len(selected_names) >= max_tools:
                break
        if len(selected_names) >= max_tools:
            break

    selected = [_TOOLS_BY_NAME[name] for name in selected_names[:max_tools] if name in _TOOLS_BY_NAME]
    return selected if selected else available


def validate_registry() -> dict[str, list[str] | int]:
    categorized = [name for names in CATEGORY_TOOL_NAMES.values() for name in names]
    categorized_set = set(categorized)
    registry_names = {tool.name for tool in ALL_INTERACTIVE_TOOLS}
    return {
        "registry_count": len(ALL_INTERACTIVE_TOOLS),
        "registry_unique_count": len(registry_names),
        "categorized_count": len(categorized),
        "categorized_unique_count": len(categorized_set),
        "missing": sorted(categorized_set - registry_names),
        "phantom": sorted(registry_names - categorized_set),
    }
