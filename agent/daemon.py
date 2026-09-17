"""Background daemon mode: runs the agent unattended, reacting to triggers
instead of waiting for direct user input.

Two trigger types are wired up as examples:
  - Scheduled (APScheduler): e.g. a daily morning briefing.
  - Filesystem (watchdog): e.g. react when a new file lands in ~/Downloads.

Extend `_handle_trigger` with whatever proactive behavior you want. Keep
every action gated through the same tools/safety path as interactive mode
— a daemon is exactly where an ungated destructive action would be worst.

Run with: python -m agent.main --daemon
"""

import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from agent import config
from agent.graph import build_graph

logging.basicConfig(
    filename=config.DAEMON_LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)

_app = build_graph()


def _handle_trigger(prompt: str):
    """Run one agent turn for a system-generated (not user-typed) prompt."""
    logging.info(f"Trigger fired: {prompt}")
    result = _app.invoke(
        {"messages": [{"role": "user", "content": prompt}], "iterations": 0}
    )
    final_message = result["messages"][-1]
    content = getattr(final_message, "content", str(final_message))
    logging.info(f"Response: {content}")
    print(f"[daemon] {content}")


class _DownloadsHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        _handle_trigger(
            f"A new file just appeared: {event.src_path}. Take a look and let "
            "me know if it needs any action (e.g. sorting, or if it looks "
            "like something risky)."
        )


def _morning_briefing():
    _handle_trigger(
        "Give me a short morning briefing: anything relevant you can check "
        "from local tools (files, memory notes). Keep it brief."
    )


def run_daemon():
    scheduler = BackgroundScheduler()
    scheduler.add_job(_morning_briefing, "cron", hour=8, minute=0)
    scheduler.start()

    observer = Observer()
    for directory in config.WATCHED_DIRECTORIES:
        observer.schedule(_DownloadsHandler(), directory, recursive=False)
    if config.WATCHED_DIRECTORIES:
        observer.start()

    print(
        f"[daemon] Running. Logging to {config.DAEMON_LOG_PATH}. "
        "Press Ctrl+C to stop."
    )
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
        if config.WATCHED_DIRECTORIES:
            observer.stop()
            observer.join()
        print("\n[daemon] Stopped.")
