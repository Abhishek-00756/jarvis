"""Install/uninstall the Jarvis daemon as a macOS LaunchAgent."""

import os
import plistlib
import subprocess
import sys
from pathlib import Path

LABEL = "com.jarvis.agent"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
LOG_DIR = Path.home() / ".jarvis_agent" / "logs"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _plist_data() -> dict:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "Label": LABEL,
        "ProgramArguments": [str(Path(sys.executable).resolve()), "-m", "agent.main", "--daemon"],
        "WorkingDirectory": str(PROJECT_ROOT),
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 10,
        "ProcessType": "Background",
        "StandardOutPath": str(LOG_DIR / "launchagent.out.log"),
        "StandardErrorPath": str(LOG_DIR / "launchagent.err.log"),
        "EnvironmentVariables": {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/opt/homebrew/sbin"},
    }


def _bootstrap() -> None:
    subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(PLIST_PATH)], check=True, capture_output=True, text=True)


def _bootout() -> None:
    subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{LABEL}"], check=True, capture_output=True, text=True)


def install() -> str:
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_bytes(plistlib.dumps(_plist_data()))
    try:
        _bootout()
    except subprocess.CalledProcessError:
        pass
    try:
        _bootstrap()
    except subprocess.CalledProcessError as exc:
        return f"LaunchAgent plist written, but bootstrap failed: {exc.stderr.strip()}"
    return f"Installed {LABEL} at {PLIST_PATH}."


def uninstall() -> str:
    try:
        _bootout()
    except subprocess.CalledProcessError:
        pass
    PLIST_PATH.unlink(missing_ok=True)
    return f"Uninstalled {LABEL}."


def status() -> str:
    result = subprocess.run(["launchctl", "print", f"gui/{os.getuid()}/{LABEL}"], capture_output=True, text=True)
    return "installed and loaded" if result.returncode == 0 else "not loaded"


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "status"
    print({"install": install, "uninstall": uninstall, "status": status}.get(command, status)())
