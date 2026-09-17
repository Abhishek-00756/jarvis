"""Tests for the confirmation gate. Uses monkeypatch to simulate user input
so these run non-interactively."""

from agent import config
from agent.safety import confirm_action, requires_confirmation


def test_requires_confirmation_for_shell():
    assert requires_confirmation("run_shell_command") is True


def test_does_not_require_confirmation_for_read_only_tool():
    assert requires_confirmation("read_file") is False


def test_confirm_action_denied(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert confirm_action("write_file", "test action") is False


def test_confirm_action_approved(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert confirm_action("write_file", "test action") is True
