"""Read-only background daemon for scheduled and filesystem-triggered checks."""

import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from agent import config
from agent.graph import build_graph, build_unattended_tools

logging.basicConfig(filename=config.DAEMON_LOG_PATH, level=logging.INFO, format="%(asctime)s %(message)s")

_app = build_graph(toolset=build_unattended_tools(), cloud_toolset=[], allow_cloud_escalation=False)


def _handle_trigger(prompt: str):
    logging.info("Read-only trigger: %s", prompt)
    result = _app.invoke({"messages": [{"role": "user", "content": prompt}], "iterations": 0, "escalated": False})
    final = result["messages"][-1]
    logging.info("Result: %s", getattr(final, "content", str(final))[:1000])


def _morning_briefing():
    _handle_trigger("Give me a short read-only morning status: calendar, open reminders, battery, disk, and any relevant tasks. Do not change anything.")


class _Handler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            _handle_trigger(f"A new file was created at {event.src_path}. Report what it is; do not modify it.")

    def on_modified(self, event):
        if not event.is_directory:
            _handle_trigger(f"A file changed at {event.src_path}. Report the change context if available; do not modify it.")


def run_daemon():
    scheduler = BackgroundScheduler()
    scheduler.add_job(_morning_briefing, "cron", hour=8, minute=0)
    scheduler.start()

    observer = Observer()
    handler = _Handler()
    for directory in config.WATCHED_DIRECTORIES:
        observer.schedule(handler, directory, recursive=False)
    observer.start()

    logging.info("Jarvis daemon running in read-only mode.")
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        observer.stop()
        scheduler.shutdown(wait=False)
    observer.join()
