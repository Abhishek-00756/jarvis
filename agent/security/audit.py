"""Small best-effort JSONL audit log for security-relevant actions."""

import json
import os
import time
from pathlib import Path

LOG_PATH = Path(os.path.expanduser("~/.jarvis_agent/action_audit.jsonl"))
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def log_action(tool: str, description: str, approved: bool, result: str = "") -> None:
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "tool": tool,
        "description": description,
        "approved": approved,
        "result": result[:500],
    }
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"[audit] unable to write audit log: {exc}", file=__import__("sys").stderr)


def read_recent_actions(limit: int = 20) -> list[dict]:
    try:
        lines = LOG_PATH.read_text(encoding="utf-8").splitlines()[-max(1, limit):]
    except (OSError, ValueError):
        return []
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def search_actions(query: str, limit: int = 50) -> list[dict]:
    q = query.lower()
    return [e for e in read_recent_actions(500) if q in json.dumps(e).lower()][:limit]
