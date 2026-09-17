"""System-level status and controls: battery, CPU/memory/disk, network,
volume, brightness, and power actions.
"""

import subprocess


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return (result.stdout or result.stderr).strip()


def _run_applescript(script: str) -> str:
    return _run(["osascript", "-e", script])


def get_battery_status() -> str:
    return _run(["pmset", "-g", "batt"])


def get_disk_usage() -> str:
    return _run(["df", "-h", "/"])


def get_memory_usage() -> str:
    return _run(["vm_stat"])


def get_cpu_usage() -> str:
    result = subprocess.run(["top", "-l", "1", "-n", "0"], capture_output=True, text=True, timeout=10)
    lines = [l for l in result.stdout.splitlines() if "CPU usage" in l]
    return lines[0] if lines else "Could not read CPU usage."


def get_uptime() -> str:
    return _run(["uptime"])


def get_network_status() -> str:
    wifi = _run_applescript('tell application "System Events" to get name of current wifi network of network preferences')
    ip = _run(["ipconfig", "getifaddr", "en0"])
    return f"Wi-Fi network: {wifi or 'unknown'}\nLocal IP: {ip or 'unknown'}"


def get_current_time_and_timezone() -> str:
    return _run(["date"])


def get_volume() -> str:
    return _run_applescript("output volume of (get volume settings)")


def set_volume(level: int) -> str:
    level = max(0, min(100, level))
    _run_applescript(f"set volume output volume {level}")
    return f"Volume set to {level}."


def mute_volume() -> str:
    _run_applescript("set volume output muted true")
    return "Muted."


def unmute_volume() -> str:
    _run_applescript("set volume output muted false")
    return "Unmuted."


def set_brightness(level: float) -> str:
    result = subprocess.run(["brightness", str(level)], capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        return "Couldn't set brightness — this needs the 'brightness' CLI tool (brew install brightness), which isn't installed."
    return f"Brightness set to {level}."


def lock_screen() -> str:
    _run(["pmset", "displaysleepnow"])
    return "Screen locked."


def sleep_mac() -> str:
    _run(["pmset", "sleepnow"])
    return "Mac is going to sleep."


def restart_mac() -> str:
    _run_applescript('tell application "System Events" to restart')
    return "Restarting..."


def shutdown_mac() -> str:
    _run_applescript('tell application "System Events" to shut down')
    return "Shutting down..."
