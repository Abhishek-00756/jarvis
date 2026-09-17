"""A simple persistent task manager."""

import json
import os
import uuid
from pathlib import Path
from agent import config
from agent.util import atomic_write_json

TASKS_FILE = os.path.join(config.MEMORY_PATH, "tasks.json")


def _load() -> list[dict]:
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE) as f:
        return json.load(f)


def _save(tasks: list[dict]) -> None:
    Path(config.MEMORY_PATH).mkdir(parents=True, exist_ok=True)
    atomic_write_json(TASKS_FILE, tasks)


def create_task(title: str, priority: str = "normal", deadline: str = "") -> str:
    tasks = _load()
    task = {"id": str(uuid.uuid4())[:8], "title": title, "priority": priority, "deadline": deadline, "status": "open"}
    tasks.append(task)
    _save(tasks)
    return f"Created task '{title}' (id: {task['id']})."


def list_tasks(include_completed: bool = False) -> str:
    tasks = _load()
    if not include_completed:
        tasks = [t for t in tasks if t["status"] != "done"]
    if not tasks:
        return "No open tasks."
    lines = [
        f"[{t['id']}] {t['title']}"
        + (f" (priority: {t['priority']})" if t["priority"] != "normal" else "")
        + (f" (due: {t['deadline']})" if t["deadline"] else "")
        + (" [DONE]" if t["status"] == "done" else "")
        for t in tasks
    ]
    return "\n".join(lines)


def complete_task(task_id: str) -> str:
    tasks = _load()
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "done"
            _save(tasks)
            return f"Marked '{t['title']}' complete."
    return f"No task found with id '{task_id}'."


def delete_task(task_id: str) -> str:
    tasks = _load()
    remaining = [t for t in tasks if t["id"] != task_id]
    if len(remaining) == len(tasks):
        return f"No task found with id '{task_id}'."
    _save(remaining)
    return f"Deleted task {task_id}."
