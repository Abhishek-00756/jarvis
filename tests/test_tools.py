"""Basic sanity tests for the non-destructive tools.

Run with: pytest tests/
"""

import tempfile
from pathlib import Path

from agent.tools import list_files, read_file, web_search_stub


def test_list_files_current_dir():
    result = list_files.invoke({"directory": "."})
    assert isinstance(result, str)


def test_read_file_roundtrip():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("hello jarvis")
        temp_path = f.name
    try:
        content = read_file.invoke({"path": temp_path})
        assert "hello jarvis" in content
    finally:
        Path(temp_path).unlink()


def test_web_search_stub_returns_placeholder():
    result = web_search_stub.invoke({"query": "test query"})
    assert "test query" in result
