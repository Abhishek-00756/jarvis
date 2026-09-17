"""Public tool registry compatibility layer.

The original Jarvis registry lives in ``agent/tools.py`` and contains a few
legacy names that were referenced in ALL_TOOLS but were never defined in that
module.  Loading it through this package lets us keep the existing registry
without rewriting the large file, while providing the missing tool objects
and correcting a few stale system-control wrappers.

All callers should continue using ``from agent.tools import ...``.
"""

from pathlib import Path
import runpy

from langchain_core.tools import tool


def _compat_tools():
    """Return tool objects required by the legacy registry but missing there."""

    @tool
    def quit_app(app_name: str) -> str:
        """Quit a macOS application. Requires confirmation."""
        from agent import config
        from agent.safety import confirm_action, requires_confirmation
        if requires_confirmation("quit_app"):
            if not confirm_action("quit_app", f"Quit {app_name}"):
                return "Action denied by user."
        from agent.computer import macos_control
        return macos_control.quit_app(app_name)

    @tool
    def click_menu_item(app_name: str, menu_name: str, item_name: str) -> str:
        """Click a menu-bar item in a macOS application. Requires confirmation."""
        from agent.safety import confirm_action, requires_confirmation
        if requires_confirmation("click_menu_item"):
            if not confirm_action("click_menu_item", f"Click {menu_name} > {item_name} in {app_name}"):
                return "Action denied by user."
        from agent.computer import macos_control
        return macos_control.click_menu_item(app_name, menu_name, item_name)

    @tool
    def browser_fill(selector: str, text: str) -> str:
        """Fill a text field in the controlled Playwright browser. Requires confirmation."""
        from agent.safety import confirm_action, requires_confirmation
        if requires_confirmation("browser_fill"):
            if not confirm_action("browser_fill", f"Fill '{selector}' with text"):
                return "Action denied by user."
        from agent.computer import browser_control
        return browser_control.browser_fill(selector, text)

    @tool
    def browser_close() -> str:
        """Close the controlled browser session."""
        from agent.computer import browser_control
        return browser_control.browser_close()

    @tool
    def get_cpu_usage() -> str:
        """Return current CPU usage."""
        from agent.system import system_control
        return system_control.get_cpu_usage()

    @tool
    def get_memory_usage() -> str:
        """Return current memory usage."""
        from agent.system import system_control
        return system_control.get_memory_usage()

    @tool
    def get_uptime() -> str:
        """Return system uptime."""
        from agent.system import system_control
        return system_control.get_uptime()

    @tool
    def get_current_time_and_timezone() -> str:
        """Return current date/time information."""
        from agent.system import system_control
        return system_control.get_current_time_and_timezone()

    @tool
    def unmute_system_volume() -> str:
        """Unmute system audio."""
        from agent.system import system_control
        return system_control.unmute_volume()

    @tool
    def set_screen_brightness(level: float) -> str:
        """Set display brightness using the macOS brightness CLI."""
        from agent.system import system_control
        return system_control.set_brightness(level)

    @tool
    def get_volume_level() -> str:
        """Return current output volume."""
        from agent.system import system_control
        return system_control.get_volume()

    @tool
    def set_volume_level(level: int) -> str:
        """Set output volume from 0 to 100. Requires confirmation."""
        from agent.safety import confirm_action, requires_confirmation
        if requires_confirmation("set_volume_level"):
            if not confirm_action("set_volume_level", f"Set volume to {level}%"):
                return "Action denied by user."
        from agent.system import system_control
        return system_control.set_volume(level)

    @tool
    def mute_system_volume() -> str:
        """Mute system audio. Requires confirmation."""
        from agent.safety import confirm_action, requires_confirmation
        if requires_confirmation("set_volume_level"):
            if not confirm_action("set_volume_level", "Mute system volume"):
                return "Action denied by user."
        from agent.system import system_control
        return system_control.mute_volume()

    return {
        t.name: t
        for t in [
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
            get_volume_level,
            set_volume_level,
            mute_system_volume,
        ]
    }


_COMPAT = _compat_tools()
_LEGACY = Path(__file__).resolve().parent.parent / "tools.py"
_namespace = runpy.run_path(str(_LEGACY), init_globals=_COMPAT)

for _name, _value in _namespace.items():
    if not _name.startswith("__"):
        globals()[_name] = _value

# Replace stale registry entries with the corrected compatibility tools.
for _registry_name in ("ALL_TOOLS", "SAFE_CLOUD_TOOLS"):
    _registry = globals().get(_registry_name, [])
    globals()[_registry_name] = [
        _COMPAT.get(getattr(_tool, "name", ""), _tool) for _tool in _registry
    ]

# Export the corrected compatibility objects by their normal names.
globals().update(_COMPAT)

__all__ = [name for name in globals() if not name.startswith("_")]
