"""Tool definitions for the Jarvis agent."""
import subprocess
from pathlib import Path
from langchain_core.tools import tool
from agent import config, memory
from agent.safety import confirm_action, requires_confirmation

@tool
def list_files(directory: str = ".") -> str:
    """List files and folders in a directory."""
    try:
        entries = sorted(Path(directory).iterdir())
        lines = []
        for p in entries:
            suffix = "/" if p.is_dir() else ""
            lines.append(f"{p.name}{suffix}")
        return "\n".join(lines) or "(empty)"
    except Exception as e:
        return f"Error listing {directory}: {e}"

@tool
def read_file(path: str) -> str:
    """Read a UTF-8 text file."""
    try:
        return Path(path).read_text()[:12000]
    except Exception as e:
        return f"Error reading {path}: {e}"

@tool
def write_file(path: str, content: str) -> str:
    """Write UTF-8 text to a file. Requires confirmation."""
    if requires_confirmation("write_file"):
        if not confirm_action("write_file", f"Write {len(content)} chars to {path}"):
            return "Action denied by user."
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content)
        return f"Wrote {len(content)} chars to {path}."
    except Exception as e:
        return f"Error writing {path}: {e}"

@tool
def delete_file(path: str) -> str:
    """Delete a file or empty directory. Requires confirmation."""
    if requires_confirmation("delete_file"):
        if not confirm_action("delete_file", f"Delete {path}"):
            return "Action denied by user."
    try:
        p = Path(path)
        if p.is_dir():
            p.rmdir()
        else:
            p.unlink()
        return f"Deleted {path}."
    except Exception as e:
        return f"Error deleting {path}: {e}"

@tool
def run_shell_command(command: str) -> str:
    """Run a shell command and return stdout/stderr. Requires confirmation."""
    if requires_confirmation("run_shell_command"):
        if not confirm_action("run_shell_command", command):
            return "Action denied by user."
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout.strip() or result.stderr.strip()
        return output[:12000] if output else f"Command exited {result.returncode}."
    except Exception as e:
        return f"Shell error: {e}"

@tool
def web_search(query: str) -> str:
    """Search the web via Tavily when TAVILY_API_KEY is configured."""
    api_key = config.TAVILY_API_KEY
    if not api_key:
        return "Web search is not configured. Set TAVILY_API_KEY in .env."
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=5)
        lines = []
        for item in response.get("results", []):
            lines.append(f"{item.get('title')}\n{item.get('content','')[:1200]}\nURL: {item.get('url','')}")
        return "\n\n".join(lines) or "No results."
    except Exception as e:
        return f"Web search error: {e}"

# --- Memory ---

@tool
def remember_fact(key: str, value: str) -> str:
    """Remember a durable fact about the user."""
    return memory.remember_fact(key, value)

@tool
def recall_fact(key: str) -> str:
    """Recall a stored fact."""
    return memory.recall_fact(key)

@tool
def remember_note(note: str) -> str:
    """Store a semantically searchable note."""
    return memory.remember_note(note)

@tool
def recall_notes(query: str, n: int = 5) -> str:
    """Search semantic memory notes."""
    return memory.recall_notes(query, n)

# --- macOS apps / UI ---

@tool
def open_app(app_name: str) -> str:
    """Open/activate a macOS application. Requires confirmation."""
    if requires_confirmation("open_app"):
        if not confirm_action("open_app", f"Open app {app_name}"):
            return "Action denied by user."
    try:
        result = subprocess.run(["open", "-a", app_name], capture_output=True, text=True, timeout=10)
        return f"Opened {app_name}." if result.returncode == 0 else result.stderr.strip()
    except Exception as e:
        return f"Error opening {app_name}: {e}"

@tool
def get_frontmost_app() -> str:
    """Return the name of the frontmost macOS application."""
    try:
        from agent.computer.macos_control import get_frontmost_app as impl
        return impl()
    except Exception as e:
        return f"Error: {e}"

@tool
def get_current_context() -> str:
    """Return a snapshot of current app, browser tab and clipboard."""
    try:
        from agent.context.context import get_current_context as impl
        return impl()
    except Exception as e:
        return f"Error getting current context: {e}"

@tool
def get_active_browser_tab() -> str:
    """Return the active tab of the user's real frontmost Safari/Chrome."""
    try:
        from agent.context.browser_context import get_active_browser_tab as impl
        return impl()
    except Exception as e:
        return f"Error: {e}"

@tool
def get_clipboard() -> str:
    """Read the system clipboard."""
    try:
        from agent.context.clipboard import get_clipboard as impl
        return impl()
    except Exception as e:
        return f"Error: {e}"

@tool
def set_clipboard(text: str) -> str:
    """Replace the system clipboard. Requires confirmation."""
    if requires_confirmation("set_clipboard"):
        if not confirm_action("set_clipboard", f"Replace clipboard with {len(text)} chars"):
            return "Action denied by user."
    try:
        from agent.context.clipboard import set_clipboard as impl
        return impl(text)
    except Exception as e:
        return f"Error: {e}"

@tool
def type_text(text: str) -> str:
    """Type text into the current macOS UI using System Events. Requires confirmation."""
    if requires_confirmation("type_text"):
        if not confirm_action("type_text", f"Type: {text[:100]}"):
            return "Action denied by user."
    try:
        from agent.computer.macos_control import type_text as impl
        return impl(text)
    except Exception as e:
        return f"Error: {e}"

@tool
def run_shortcut(name: str) -> str:
    """Run a macOS Shortcut by name. Requires confirmation."""
    if requires_confirmation("run_shortcut"):
        if not confirm_action("run_shortcut", f"Run Shortcut: {name}"):
            return "Action denied by user."
    try:
        result = subprocess.run(["shortcuts", "run", name], capture_output=True, text=True, timeout=60)
        return (result.stdout.strip() or result.stderr.strip())[:4000]
    except Exception as e:
        return f"Shortcut error: {e}"

@tool
def whatsapp_call(contact: str) -> str:
    """Call a WhatsApp contact by name/number. Requires confirmation."""
    if requires_confirmation("whatsapp_call"):
        if not confirm_action("whatsapp_call", f"WhatsApp call {contact}"):
            return "Action denied by user."
    from agent.computer.whatsapp_control import whatsapp_call as impl
    return impl(contact)

@tool
def whatsapp_send_message(contact: str, message: str) -> str:
    """Send a WhatsApp message. Requires confirmation."""
    if requires_confirmation("whatsapp_send_message"):
        if not confirm_action("whatsapp_send_message", f"WhatsApp to {contact}: {message}"):
            return "Action denied by user."
    from agent.computer.whatsapp_control import whatsapp_send_message as impl
    return impl(contact, message)

@tool
def inspect_app_ui(app_name: str = "") -> str:
    """Inspect accessibility UI elements of an app for diagnostics."""
    try:
        from agent.computer.macos_control import inspect_app_ui as impl
        return impl(app_name)
    except Exception as e:
        return f"Error: {e}"

# --- Apple built-in apps ---

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send email through Apple Mail. Requires confirmation."""
    if requires_confirmation("send_email"):
        if not confirm_action("send_email", f"Send email to {to}: {subject}"):
            return "Action denied by user."
    from agent.computer.apple_apps import send_email as impl
    return impl(to, subject, body)

@tool
def get_calendar_events_today() -> str:
    """List today's Calendar events. Read-only."""
    from agent.computer.apple_apps import get_calendar_events_today as impl
    return impl()

@tool
def add_calendar_event(title: str, start_date_str: str, end_date_str: str, calendar_name: str = "") -> str:
    """Add a calendar event. Requires confirmation."""
    if requires_confirmation("add_calendar_event"):
        if not confirm_action("add_calendar_event", f"Calendar event {title} {start_date_str}-{end_date_str}"):
            return "Action denied by user."
    from agent.computer.apple_apps import add_calendar_event as impl
    return impl(title, start_date_str, end_date_str, calendar_name)

@tool
def add_reminder(text: str, list_name: str = "Reminders", due_date_str: str = "") -> str:
    """Add a Reminder. Requires confirmation."""
    if requires_confirmation("add_reminder"):
        if not confirm_action("add_reminder", f"Reminder: {text}"):
            return "Action denied by user."
    from agent.computer.apple_apps import add_reminder as impl
    return impl(text, list_name, due_date_str)

@tool
def add_note(title: str, body: str) -> str:
    """Create a note in Apple Notes. Requires confirmation."""
    if requires_confirmation("add_note"):
        if not confirm_action("add_note", f"Create note: {title}"):
            return "Action denied by user."
    from agent.computer.apple_apps import add_note as impl
    return impl(title, body)

# --- Browser ---

@tool
def browser_navigate(url: str) -> str:
    """Navigate the controlled Playwright browser. Requires confirmation."""
    if requires_confirmation("browser_navigate"):
        if not confirm_action("browser_navigate", f"Navigate browser to {url}"):
            return "Action denied by user."
    from agent.computer.browser_control import browser_navigate as impl
    return impl(url)

@tool
def browser_go_to(destination: str) -> str:
    """Navigate the controlled browser to a named shortcut such as instagram_reels."""
    if requires_confirmation("browser_navigate"):
        if not confirm_action("browser_navigate", f"Navigate browser to shortcut {destination}"):
            return "Action denied by user."
    from agent.computer.browser_control import browser_navigate_shortcut
    return browser_navigate_shortcut(destination)

@tool
def browser_get_text() -> str:
    """Read visible text from the controlled browser page."""
    from agent.computer.browser_control import browser_get_text as impl
    return impl()

@tool
def browser_get_current_url() -> str:
    """Return current URL in the controlled browser."""
    from agent.computer.browser_control import browser_get_current_url as impl
    return impl()

@tool
def browser_click(selector: str) -> str:
    """Click a CSS selector in the controlled browser. Requires confirmation."""
    if requires_confirmation("browser_click"):
        if not confirm_action("browser_click", f"Click browser selector: {selector}"):
            return "Action denied by user."
    from agent.computer.browser_control import browser_click as impl
    return impl(selector)

@tool
def share_reel_to_instagram_dm(recipient_username: str, message: str = "") -> str:
    """Share current Instagram reel to a user's DM. Requires confirmation."""
    if requires_confirmation("share_reel_to_instagram_dm"):
        if not confirm_action("share_reel_to_instagram_dm", f"Share reel to {recipient_username}"):
            return "Action denied by user."
    from agent.computer.browser_control import share_reel_to_instagram_dm as impl
    return impl(recipient_username, message)

@tool
def browser_inspect_page() -> str:
    """Dump accessible roles/names from current browser page."""
    from agent.computer.browser_control import browser_inspect_page as impl
    return impl()

@tool
def ask_cloud_model(prompt: str) -> str:
    """Explicitly ask the optional cloud model a question. Only safe/read-only tools are bound in graph escalation."""
    if not config.CLOUD_FALLBACK_ENABLED:
        return "Cloud fallback is not configured."
    try:
        from agent.llm import get_cloud_llm
        llm = get_cloud_llm()
        return llm.invoke(prompt).content
    except Exception as e:
        return f"Cloud model error: {e}"

# --- system controls ---

@tool
def get_battery_status() -> str:
    """Return current battery status."""
    from agent.system.system_control import get_battery_status as impl
    return impl()

@tool
def get_disk_usage() -> str:
    """Return root disk usage."""
    from agent.system.system_control import get_disk_usage as impl
    return impl()

@tool
def get_network_status() -> str:
    """Return current network status."""
    from agent.system.system_control import get_network_status as impl
    return impl()

@tool
def get_volume_level() -> str:
    """Return system volume level."""
    from agent.system.system_control import get_volume_level as impl
    return impl()

@tool
def set_volume_level(level: int) -> str:
    """Set volume from 0-100. Requires confirmation."""
    if requires_confirmation("set_volume_level"):
        if not confirm_action("set_volume_level", f"Set volume to {level}%"):
            return "Action denied by user."
    from agent.system.system_control import set_volume_level as impl
    return impl(level)

@tool
def mute_system_volume() -> str:
    """Mute system volume. Requires confirmation."""
    if requires_confirmation("set_volume_level"):
        if not confirm_action("set_volume_level", "Mute system volume"):
            return "Action denied by user."
    from agent.system.system_control import mute_system_volume as impl
    return impl()

@tool
def lock_screen() -> str:
    """Lock the Mac. Requires confirmation."""
    if requires_confirmation("lock_screen"):
        if not confirm_action("lock_screen", "Lock the Mac now"):
            return "Action denied by user."
    from agent.system.system_control import lock_screen as impl
    return impl()

@tool
def sleep_mac() -> str:
    """Put the Mac to sleep. Requires confirmation."""
    if requires_confirmation("sleep_mac"):
        if not confirm_action("sleep_mac", "Put the Mac to sleep"):
            return "Action denied by user."
    from agent.system.system_control import sleep_mac as impl
    return impl()

@tool
def restart_mac() -> str:
    """Restart the Mac. Requires confirmation."""
    if requires_confirmation("restart_mac"):
        if not confirm_action("restart_mac", "Restart the Mac"):
            return "Action denied by user."
    from agent.system.system_control import restart_mac as impl
    return impl()

@tool
def shutdown_mac() -> str:
    """Shut down the Mac. Requires confirmation."""
    if requires_confirmation("shutdown_mac"):
        if not confirm_action("shutdown_mac", "Shut down the Mac"):
            return "Action denied by user."
    from agent.system.system_control import shutdown_mac as impl
    return impl()

# --- Window management ---

@tool
def list_open_windows(app_name: str = "") -> str:
    """List open windows, optionally for one application."""
    from agent.computer.macos_control import list_open_windows as impl
    return impl(app_name)

@tool
def close_window(window_id: int = 0) -> str:
    """Close a window by id. Requires confirmation."""
    if requires_confirmation("close_window"):
        if not confirm_action("close_window", f"Close window {window_id}"):
            return "Action denied by user."
    from agent.computer.macos_control import close_window as impl
    return impl(window_id)

@tool
def minimize_window(window_id: int = 0) -> str:
    """Minimize a window by id."""
    from agent.computer.macos_control import minimize_window as impl
    return impl(window_id)

@tool
def maximize_window(window_id: int = 0) -> str:
    """Zoom/maximize a window by id."""
    from agent.computer.macos_control import maximize_window as impl
    return impl(window_id)

@tool
def move_window(window_id: int, x: int, y: int) -> str:
    """Move a window. Requires confirmation."""
    if requires_confirmation("move_window"):
        if not confirm_action("move_window", f"Move window {window_id} to ({x},{y})"):
            return "Action denied by user."
    from agent.computer.macos_control import move_window as impl
    return impl(window_id, x, y)

@tool
def resize_window(window_id: int, width: int, height: int) -> str:
    """Resize a window."""
    from agent.computer.macos_control import resize_window as impl
    return impl(window_id, width, height)

# --- Finder/file management ---

@tool
def find_file(pattern: str, directory: str = "~") -> str:
    """Recursively find file paths matching a case-insensitive name pattern."""
    from agent.computer.finder_control import find_file as impl
    return impl(pattern, directory)

@tool
def search_file_content(pattern: str, directory: str = "~") -> str:
    """Search UTF-8 file contents using grep. Read-only."""
    from agent.computer.finder_control import search_file_content as impl
    return impl(pattern, directory)

@tool
def get_recent_files(directory: str = "~/Downloads", limit: int = 20) -> str:
    """Return recently modified files in a directory."""
    from agent.computer.finder_control import get_recent_files as impl
    return impl(directory, limit)

@tool
def get_file_info(path: str) -> str:
    """Return file metadata."""
    from agent.computer.finder_control import get_file_info as impl
    return impl(path)

@tool
def move_file(src: str, dst: str) -> str:
    """Move a file/folder. Requires confirmation."""
    if requires_confirmation("move_file"):
        if not confirm_action("move_file", f"Move {src} -> {dst}"):
            return "Action denied by user."
    from agent.computer.finder_control import move_file as impl
    return impl(src, dst)

@tool
def copy_file(src: str, dst: str) -> str:
    """Copy a file/folder. Requires confirmation."""
    if requires_confirmation("copy_file"):
        if not confirm_action("copy_file", f"Copy {src} -> {dst}"):
            return "Action denied by user."
    from agent.computer.finder_control import copy_file as impl
    return impl(src, dst)

@tool
def rename_file(path: str, new_name: str) -> str:
    """Rename a file/folder. Requires confirmation."""
    if requires_confirmation("rename_file"):
        if not confirm_action("rename_file", f"Rename {path} -> {new_name}"):
            return "Action denied by user."
    from agent.computer.finder_control import rename_file as impl
    return impl(path, new_name)

@tool
def create_folder(path: str) -> str:
    """Create a folder tree."""
    from agent.computer.finder_control import create_folder as impl
    return impl(path)

@tool
def trash_file(path: str) -> str:
    """Move a file to Trash. Requires confirmation."""
    if requires_confirmation("trash_file"):
        if not confirm_action("trash_file", f"Move {path} to Trash"):
            return "Action denied by user."
    from agent.computer.finder_control import trash_file as impl
    return impl(path)

@tool
def reveal_in_finder(path: str) -> str:
    """Reveal a path in Finder."""
    from agent.computer.finder_control import reveal_in_finder as impl
    return impl(path)

@tool
def open_file(path: str) -> str:
    """Open a file with macOS default application. Requires confirmation."""
    if requires_confirmation("open_file"):
        if not confirm_action("open_file", f"Open {path}"):
            return "Action denied by user."
    from agent.computer.finder_control import open_file as impl
    return impl(path)

@tool
def compress_file(path: str, output_path: str = "") -> str:
    """Compress a file/folder into a zip archive."""
    from agent.computer.finder_control import compress_file as impl
    return impl(path, output_path)

@tool
def extract_archive(path: str, output_dir: str = "") -> str:
    """Extract an archive into a directory. Requires confirmation."""
    if requires_confirmation("extract_archive"):
        if not confirm_action("extract_archive", f"Extract {path}"):
            return "Action denied by user."
    from agent.computer.finder_control import extract_archive as impl
    return impl(path, output_dir)

# --- Documents ---

@tool
def read_pdf(path: str) -> str:
    """Extract text from a PDF."""
    from agent.documents.extractor import read_pdf as impl
    return impl(path)

@tool
def search_pdf(path: str, query: str) -> str:
    """Search for text in a PDF."""
    from agent.documents.extractor import search_pdf as impl
    return impl(path, query)

@tool
def read_docx(path: str) -> str:
    """Extract text from a DOCX."""
    from agent.documents.extractor import read_docx as impl
    return impl(path)

@tool
def read_pptx(path: str) -> str:
    """Extract text from a PPTX."""
    from agent.documents.extractor import read_pptx as impl
    return impl(path)

@tool
def read_spreadsheet(path: str) -> str:
    """Extract sheet names and cell data from a spreadsheet."""
    from agent.documents.extractor import read_spreadsheet as impl
    return impl(path)

# --- Calendar / reminders / notes / mail / contacts ---

@tool
def get_calendar_events_range(start_date: str, end_date: str) -> str:
    """List Calendar events in a date range."""
    from agent.computer.apple_apps import get_calendar_events_range as impl
    return impl(start_date, end_date)

@tool
def find_event(query: str) -> str:
    """Find calendar events by title/text."""
    from agent.computer.apple_apps import find_event as impl
    return impl(query)

@tool
def list_reminders(list_name: str = "") -> str:
    """List reminders, optionally within a list."""
    from agent.computer.apple_apps import list_reminders as impl
    return impl(list_name)

@tool
def complete_reminder(query: str) -> str:
    """Complete the first matching reminder."""
    from agent.computer.apple_apps import complete_reminder as impl
    return impl(query)

@tool
def delete_reminder(query: str) -> str:
    """Delete a matching reminder. Requires confirmation."""
    if requires_confirmation("delete_reminder"):
        if not confirm_action("delete_reminder", f"Delete reminder matching {query}"):
            return "Action denied by user."
    from agent.computer.apple_apps import delete_reminder as impl
    return impl(query)

@tool
def search_notes(query: str) -> str:
    """Search Apple Notes."""
    from agent.computer.apple_apps import search_notes as impl
    return impl(query)

@tool
def read_note(title: str) -> str:
    """Read a Note by title."""
    from agent.computer.apple_apps import read_note as impl
    return impl(title)

@tool
def append_note(title: str, text: str) -> str:
    """Append text to an existing note. Requires confirmation."""
    if requires_confirmation("append_note"):
        if not confirm_action("append_note", f"Append to note {title}"):
            return "Action denied by user."
    from agent.computer.apple_apps import append_note as impl
    return impl(title, text)

@tool
def get_unread_emails() -> str:
    """List unread mail subject/sender snippets."""
    from agent.computer.apple_apps import get_unread_emails as impl
    return impl()

@tool
def search_emails(query: str) -> str:
    """Search Mail subject/sender/body using a broad AppleScript filter."""
    from agent.computer.apple_apps import search_emails as impl
    return impl(query)

@tool
def search_contact(query: str) -> str:
    """Search Contacts for a name/email/phone."""
    from agent.computer.apple_apps import search_contact as impl
    return impl(query)

# --- Media ---

@tool
def media_play() -> str:
    """Play Music.app."""
    from agent.computer.media_control import play
    return play()

@tool
def media_pause() -> str:
    """Pause Music.app."""
    from agent.computer.media_control import pause
    return pause()

@tool
def media_next_track() -> str:
    """Skip to next Music.app track."""
    from agent.computer.media_control import next_track
    return next_track()

@tool
def media_previous_track() -> str:
    """Go to previous Music.app track."""
    from agent.computer.media_control import previous_track
    return previous_track()

@tool
def media_current_track() -> str:
    """Return current Music.app track."""
    from agent.computer.media_control import current_track
    return current_track()

# --- Generalized messaging ---

@tool
def send_imessage(recipient: str, message: str) -> str:
    """Send an iMessage/SMS. Requires confirmation."""
    if requires_confirmation("send_imessage"):
        if not confirm_action("send_imessage", f"Send iMessage to {recipient}: {message}"):
            return "Action denied by user."
    from agent.computer import messaging
    return messaging.send_imessage(recipient, message)

@tool
def send_message(platform: str, person: str, message: str) -> str:
    """Send a message to someone on a given platform ('whatsapp' or 'imessage').
    Prefer this over the platform-specific tools when the user just says
    "message X" without specifying a platform and iMessage is more reliable
    for that contact. Requires confirmation."""
    if requires_confirmation("send_message"):
        if not confirm_action("send_message", f"Send {platform} message to {person}: {message}"):
            return "Action denied by user."
    from agent.computer import messaging
    return messaging.send_message(platform, person, message)

# --- Task manager ---

@tool
def create_task(title: str, priority: str = "normal", deadline: str = "") -> str:
    """Create a task to track. Does not require confirmation."""
    from agent import tasks
    return tasks.create_task(title, priority, deadline)

@tool
def list_tasks() -> str:
    """List open tasks. Read-only."""
    from agent import tasks
    return tasks.list_tasks()

@tool
def complete_task(task_id: str) -> str:
    """Mark a task complete by its id. Does not require confirmation."""
    from agent import tasks
    return tasks.complete_task(task_id)

@tool
def delete_task(task_id: str) -> str:
    """Delete a task by its id. Does not require confirmation."""
    from agent import tasks
    return tasks.delete_task(task_id)

# --- Audit log ---

@tool
def what_did_you_do_today() -> str:
    """Show recent actions Jarvis has taken (from the audit log). Read-only."""
    from agent.security.audit import read_recent_actions
    entries = read_recent_actions(20)
    if not entries:
        return "No actions logged yet."
    return "\n".join(
        f"{e['timestamp']}: {e['tool']} - {e['description']} "
        f"({'approved' if e['approved'] else 'denied'})"
        for e in entries
    )

ALL_TOOLS = [
    list_files,
    read_file,
    write_file,
    delete_file,
    run_shell_command,
    web_search,
    remember_fact,
    recall_fact,
    remember_note,
    recall_notes,
    open_app,
    get_frontmost_app,
    get_current_context,
    get_active_browser_tab,
    get_clipboard,
    set_clipboard,
    type_text,
    run_shortcut,
    whatsapp_call,
    whatsapp_send_message,
    inspect_app_ui,
    send_email,
    get_calendar_events_today,
    add_calendar_event,
    add_reminder,
    add_note,
    browser_navigate,
    browser_go_to,
    browser_get_text,
    browser_get_current_url,
    browser_click,
    share_reel_to_instagram_dm,
    browser_inspect_page,
    ask_cloud_model,
    get_battery_status,
    get_disk_usage,
    get_network_status,
    get_volume_level,
    set_volume_level,
    mute_system_volume,
    lock_screen,
    sleep_mac,
    restart_mac,
    shutdown_mac,
    list_open_windows,
    close_window,
    minimize_window,
    maximize_window,
    move_window,
    resize_window,
    find_file,
    search_file_content,
    get_recent_files,
    get_file_info,
    move_file,
    copy_file,
    rename_file,
    create_folder,
    trash_file,
    reveal_in_finder,
    open_file,
    compress_file,
    extract_archive,
    read_pdf,
    search_pdf,
    read_docx,
    read_pptx,
    read_spreadsheet,
    get_calendar_events_range,
    find_event,
    list_reminders,
    complete_reminder,
    delete_reminder,
    search_notes,
    read_note,
    append_note,
    get_unread_emails,
    search_emails,
    search_contact,
    media_play,
    media_pause,
    media_next_track,
    media_previous_track,
    media_current_track,
    send_imessage,
    send_message,
    create_task,
    list_tasks,
    complete_task,
    delete_task,
    what_did_you_do_today,
    quit_app,
    click_menu_item,
    browser_fill,
    browser_close,
    get_cpu_usage,
    get_memory_usage,
    get_uptime,
    get_current_time_and_timezone,
    unmute_system_volume,
    set_screen_brightness,
]

SAFE_CLOUD_TOOLS = [
    list_files,
    read_file,
    web_search,
    recall_fact,
    recall_notes,
    get_frontmost_app,
    get_current_context,
    get_active_browser_tab,
    get_clipboard,
    browser_get_text,
    get_calendar_events_today,
    get_calendar_events_range,
    list_reminders,
    search_notes,
    read_note,
    get_unread_emails,
    search_emails,
    search_contact,
    read_pdf,
    read_docx,
    read_pptx,
    read_spreadsheet,
    get_battery_status,
    get_disk_usage,
    get_network_status,
    list_tasks,
    what_did_you_do_today,
    get_cpu_usage,
    get_memory_usage,
    get_uptime,
    get_current_time_and_timezone,
]
