"""Browser control via Playwright, with a persistent profile.

Kept separate from macos_control.py because browser automation works via
the DOM (near-100% click accuracy on standard pages) rather than the
Accessibility tree.

Uses launch_persistent_context pointed at a real profile directory on disk,
so logins (Instagram, WhatsApp Web, etc.) survive between runs instead of
starting logged-out every time. First time you visit a site that needs
login, log in manually in the visible browser window that opens — after
that, the session cookie is reused automatically.

Run `playwright install chromium` once after pip-installing requirements.
"""

import os
from playwright.sync_api import sync_playwright

_playwright = None
_context = None
_page = None
_PROFILE_DIR = os.path.expanduser("~/.jarvis_agent/browser_profile")
DIRECT_URLS = {
    "instagram_reels": "https://www.instagram.com/reels/",
    "instagram_home": "https://www.instagram.com/",
    "instagram_dms": "https://www.instagram.com/direct/inbox/",
}


def _ensure_browser():
    global _playwright, _context, _page
    if _page is not None:
        return _page
    os.makedirs(_PROFILE_DIR, exist_ok=True)
    _playwright = sync_playwright().start()
    _context = _playwright.chromium.launch_persistent_context(_PROFILE_DIR, headless=False)
    _page = _context.pages[0] if _context.pages else _context.new_page()
    return _page


def browser_navigate(url: str) -> str:
    page = _ensure_browser()
    page.goto(url, wait_until="domcontentloaded")
    return f"Navigated to {url}. Title: {page.title()}"


def browser_navigate_shortcut(destination: str) -> str:
    url = DIRECT_URLS.get(destination)
    if not url:
        return f"Unknown shortcut '{destination}'. Known shortcuts: {list(DIRECT_URLS.keys())}"
    return browser_navigate(url)


def browser_get_text() -> str:
    page = _ensure_browser()
    return page.inner_text("body")[:4000]


def browser_get_current_url() -> str:
    return _ensure_browser().url


def browser_click(selector: str) -> str:
    _ensure_browser().click(selector, timeout=5000)
    return f"Clicked element matching '{selector}'."


def browser_fill(selector: str, text: str) -> str:
    _ensure_browser().fill(selector, text, timeout=5000)
    return f"Filled '{selector}' with text."


def browser_close() -> str:
    global _context, _playwright, _page
    if _context is not None:
        _context.close(); _playwright.stop()
        _context = None; _playwright = None; _page = None
    return "Browser closed."


SHARE_BUTTON_NAMES = ["Share", "Share Post"]
SEARCH_PLACEHOLDER_PATTERN = "Search"
SEND_BUTTON_NAMES = ["Send"]


def share_reel_to_instagram_dm(recipient_username: str, message: str = "") -> str:
    page = _ensure_browser()
    share_button = None
    for name in SHARE_BUTTON_NAMES:
        try:
            btn = page.get_by_role("button", name=name).first
            if btn.is_visible(timeout=2000): share_button = btn; break
        except Exception: continue
    if share_button is None:
        return "Couldn't find the Share button on the current page. Make sure a reel is open, then run browser_inspect_page()."
    share_button.click()
    try:
        search_box = page.get_by_placeholder(SEARCH_PLACEHOLDER_PATTERN).first
        search_box.wait_for(timeout=4000); search_box.fill(recipient_username); page.wait_for_timeout(1200)
    except Exception as e:
        return f"Share dialog opened, but couldn't find the search box: {e}"
    try:
        page.get_by_text(recipient_username, exact=False).first.click(timeout=3000)
    except Exception as e:
        return f"Searched for '{recipient_username}' but couldn't find/click a matching result: {e}"
    if message:
        try: page.get_by_role("textbox").last.fill(message)
        except Exception: pass
    try:
        send_button = None
        for name in SEND_BUTTON_NAMES:
            try:
                btn = page.get_by_role("button", name=name).first
                if btn.is_visible(timeout=2000): send_button = btn; break
            except Exception: continue
        if send_button is None: return f"Selected {recipient_username} but couldn't find the Send button."
        send_button.click()
    except Exception as e: return f"Selected {recipient_username} but sending failed: {e}"
    return f"Shared the reel to {recipient_username} via Instagram DM."


def browser_inspect_page() -> str:
    page = _ensure_browser(); elements = []
    for role in ("button", "link", "textbox"):
        try:
            locator = page.get_by_role(role); count = min(locator.count(), 30)
            for i in range(count):
                try:
                    name = locator.nth(i).get_attribute("aria-label") or locator.nth(i).inner_text()
                    if name: elements.append(f"{role}: {name.strip()[:60]}")
                except Exception: continue
        except Exception: continue
    return "\n".join(elements) if elements else "No labeled elements found."
