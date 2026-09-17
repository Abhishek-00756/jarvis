"""Additional tools that complement the legacy tool registry.

These are kept separate so the security execution gateway in graph.py can
wrap both the existing tools and these newer screen/browser/mail capabilities.
"""

import subprocess
from pathlib import Path

from langchain_core.tools import tool


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


# --- Screen / OCR ---

@tool
def read_screen_text() -> str:
    """Read visible text from the current Mac screen using Apple Vision OCR."""
    from agent.context.screen import read_screen_text as impl
    return impl()


@tool
def find_text_on_screen(query: str) -> str:
    """Find OCR text on the current screen containing the query."""
    from agent.context.screen import find_text_on_screen as impl
    return impl(query)


@tool
def get_screen_context() -> str:
    """Return OCR text from the current screen as context."""
    from agent.context.screen import get_screen_context as impl
    return impl()


# --- Browser completion ---

def _page():
    from agent.computer import browser_control as bc
    return bc._ensure_browser(), bc


@tool
def browser_new_tab(url: str = "") -> str:
    """Open a new tab in the controlled Playwright browser."""
    _current, bc = _page()
    page = bc._context.new_page()
    bc._page = page
    if url:
        page.goto(url, wait_until="domcontentloaded")
    return f"Opened browser tab {len(bc._context.pages) - 1}" + (f" at {url}." if url else ".")


@tool
def browser_list_tabs() -> str:
    """List tabs in the controlled browser with index, title and URL."""
    _current, bc = _page()
    rows = []
    for i, page in enumerate(bc._context.pages):
        try:
            rows.append(f"{i}: {page.title()} — {page.url}")
        except Exception:
            rows.append(f"{i}: <unavailable>")
    return "\n".join(rows) if rows else "No browser tabs."


@tool
def browser_switch_tab(index: int) -> str:
    """Switch the controlled browser to a tab by zero-based index."""
    _current, bc = _page()
    pages = bc._context.pages
    if index < 0 or index >= len(pages):
        return f"Invalid tab index {index}."
    bc._page = pages[index]
    pages[index].bring_to_front()
    return f"Switched to tab {index}: {pages[index].url}"


@tool
def browser_close_tab(index: int = -1) -> str:
    """Close a controlled browser tab by index."""
    _current, bc = _page()
    pages = bc._context.pages
    if not pages:
        return "No browser tabs."
    if index < 0:
        index = len(pages) - 1
    if index < 0 or index >= len(pages):
        return f"Invalid tab index {index}."
    pages[index].close()
    remaining = bc._context.pages
    bc._page = remaining[0] if remaining else None
    return f"Closed tab {index}."


@tool
def browser_back() -> str:
    """Go back in browser history."""
    page, _ = _page()
    page.go_back(wait_until="domcontentloaded")
    return f"Back: {page.url}"


@tool
def browser_forward() -> str:
    """Go forward in browser history."""
    page, _ = _page()
    page.go_forward(wait_until="domcontentloaded")
    return f"Forward: {page.url}"


@tool
def browser_reload() -> str:
    """Reload the current browser page."""
    page, _ = _page()
    page.reload(wait_until="domcontentloaded")
    return f"Reloaded: {page.url}"


@tool
def browser_scroll(delta_y: int = 600) -> str:
    """Scroll the current page vertically by the requested pixels."""
    page, _ = _page()
    page.evaluate("(y) => window.scrollBy(0, y)", delta_y)
    return f"Scrolled by {delta_y}px."


@tool
def browser_select(selector: str, value: str) -> str:
    """Select an option in a page select element."""
    page, _ = _page()
    page.select_option(selector, value=value, timeout=5000)
    return f"Selected '{value}' in '{selector}'."


@tool
def browser_press_key(key: str) -> str:
    """Press a keyboard key in the controlled browser."""
    page, _ = _page()
    page.keyboard.press(key)
    return f"Pressed {key}."


@tool
def browser_get_links() -> str:
    """List visible links and their hrefs on the current page."""
    page, _ = _page()
    links = page.locator("a")
    rows = []
    for i in range(min(links.count(), 80)):
        try:
            loc = links.nth(i)
            text = (loc.inner_text() or loc.get_attribute("aria-label") or "").strip().replace("\n", " ")
            href = loc.get_attribute("href") or ""
            if text or href:
                rows.append(f"{text[:100]} — {href}")
        except Exception:
            continue
    return "\n".join(rows) if rows else "No visible links found."


@tool
def browser_download(selector_or_url: str, suggested_filename: str = "") -> str:
    """Download a file by clicking a selector or opening a direct URL."""
    page, _ = _page()
    target_dir = Path.home() / ".jarvis_agent" / "downloads"
    target_dir.mkdir(parents=True, exist_ok=True)
    with page.expect_download(timeout=30000) as download_info:
        if selector_or_url.startswith(("http://", "https://")):
            page.goto(selector_or_url, wait_until="domcontentloaded")
        else:
            page.click(selector_or_url, timeout=5000)
    download = download_info.value
    name = Path(suggested_filename or download.suggested_filename or "download").name
    destination = target_dir / name
    counter = 1
    while destination.exists():
        destination = target_dir / f"{Path(name).stem}-{counter}{Path(name).suffix}"
        counter += 1
    download.save_as(str(destination))
    return f"Downloaded to {destination}."


# --- Mail write-side ---

def _mail_script(script: str) -> str:
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=30)
    return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr.strip()}"


@tool
def draft_email(to: str, subject: str, body: str) -> str:
    """Create an unsent Mail draft."""
    script = f'''tell application "Mail"
set newMsg to make new outgoing message with properties {{subject:"{_escape(subject)}", content:"{_escape(body)}", visible:true}}
tell newMsg
make new to recipient with properties {{address:"{_escape(to)}"}}
end tell
end tell
return "Draft created for {_escape(to)}."'''
    return _mail_script(script)


@tool
def reply_email(query: str, body: str) -> str:
    """Reply to the first inbox message whose subject or sender matches query."""
    script = f'''tell application "Mail"
set q to "{_escape(query)}"
repeat with a in accounts
try
set ms to every message of inbox of a whose subject contains q or sender contains q
if (count of ms) > 0 then
set r to reply (item 1 of ms) with opening window
set content of r to "{_escape(body)}"
send r
return "Replied to the first matching message."
end if
end try
end repeat
return "No matching email found."
end tell'''
    return _mail_script(script)


@tool
def forward_email(query: str, to: str, body: str = "") -> str:
    """Forward the first inbox message matching query to an address."""
    content = _escape(body)
    script = f'''tell application "Mail"
set q to "{_escape(query)}"
repeat with a in accounts
try
set ms to every message of inbox of a whose subject contains q or sender contains q
if (count of ms) > 0 then
set f to forward (item 1 of ms) with opening window
make new to recipient at f with properties {{address:"{_escape(to)}"}}
{'set content of f to "' + content + '"' if body else ''}
send f
return "Forwarded the first matching message."
end if
end try
end repeat
return "No matching email found."
end tell'''
    return _mail_script(script)


@tool
def mark_email_read(query: str) -> str:
    """Mark the first matching inbox message as read."""
    return _mail_mark(query, "true")


@tool
def mark_email_unread(query: str) -> str:
    """Mark the first matching inbox message as unread."""
    return _mail_mark(query, "false")


def _mail_mark(query: str, status: str) -> str:
    script = f'''tell application "Mail"
set q to "{_escape(query)}"
repeat with a in accounts
try
set ms to every message of inbox of a whose subject contains q or sender contains q
if (count of ms) > 0 then
set read status of item 1 of ms to {status}
return "Updated matching email read status."
end if
end try
end repeat
return "No matching email found."
end tell'''
    return _mail_script(script)


@tool
def archive_email(query: str) -> str:
    """Move the first matching inbox message to an Archive mailbox."""
    script = f'''tell application "Mail"
set q to "{_escape(query)}"
repeat with a in accounts
try
set ms to every message of inbox of a whose subject contains q or sender contains q
if (count of ms) > 0 then
repeat with b in mailboxes of a
if (name of b as string) is "Archive" then
move item 1 of ms to b
return "Archived the first matching email."
end if
end repeat
end if
end try
end repeat
return "No matching email found, or no Archive mailbox is available."
end tell'''
    return _mail_script(script)


EXTRA_TOOLS = [
    read_screen_text, find_text_on_screen, get_screen_context,
    browser_new_tab, browser_list_tabs, browser_switch_tab, browser_close_tab,
    browser_back, browser_forward, browser_reload, browser_scroll,
    browser_select, browser_press_key, browser_get_links, browser_download,
    draft_email, reply_email, forward_email, mark_email_read, mark_email_unread,
    archive_email,
]

UNATTENDED_NAMES = {
    "list_files", "read_file", "find_file", "search_file_content", "get_recent_files",
    "get_file_info", "recall_fact", "recall_notes", "read_pdf", "search_pdf",
    "read_docx", "read_pptx", "read_spreadsheet", "list_tasks", "get_cpu_usage",
    "get_memory_usage", "get_uptime", "get_current_time_and_timezone",
    "read_screen_text", "get_screen_context", "browser_get_text", "browser_get_current_url",
}
