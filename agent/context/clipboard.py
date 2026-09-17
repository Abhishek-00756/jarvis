"""Clipboard access via macOS's built-in pbcopy/pbpaste — no extra
dependencies needed. Small feature, outsized daily usefulness: it's what
makes "summarize what I just copied" or "send what I copied to X" work.
"""

import subprocess


def get_clipboard() -> str:
    """Return the current text contents of the clipboard."""
    result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
    return result.stdout


def set_clipboard(text: str) -> str:
    """Set the clipboard contents to `text`."""
    subprocess.run(["pbcopy"], input=text, text=True, timeout=5)
    return f"Copied {len(text)} characters to clipboard."
