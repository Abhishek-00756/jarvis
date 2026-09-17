"""Minimal tool smoke tests; run with pytest from repo root."""
import os

import pytest

from agent.tools import list_files, read_file, web_search


def test_list_files(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    result = list_files(str(tmp_path))
    assert "a.txt" in result


def test_read_file(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("hello world")
    assert read_file(str(p)) == "hello world"


def test_web_search_without_api_key_returns_clear_placeholder(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    # The actual module config is loaded at import time; this test is only
    # about the documented no-key behaviour, so patch the function's module
    # constant too.
    import agent.tools as tools_module
    monkeypatch.setattr(tools_module.config, "TAVILY_API_KEY", "")
    result = web_search("test query")
    assert "TAVILY_API_KEY" in result or "not configured" in result.lower()
