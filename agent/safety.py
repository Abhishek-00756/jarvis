"""Confirmation gate for impactful actions."""
from agent import config

def requires_confirmation(tool_name: str) -> bool:
    return tool_name in config.CONFIRM_REQUIRED_TOOLS

def confirm_action(tool_name: str, description: str) -> bool:
    print(f"[CONFIRM NEEDED] Tool: {tool_name}")
    print(f"  Action: {description}")
    answer = input("  Allow this action? [y/N]: ").strip().lower()
    return answer == "y"
