# Jarvis Agent — Complete Local Assistant

A local-first autonomous agent for macOS (Apple Silicon), built in five layers: text reasoning core, voice I/O, computer/browser control, long-term memory + background autonomy, and optional cloud fallback for hard reasoning.

Everything runs on your Mac by default; nothing leaves the machine unless you explicitly configure cloud fallback or web search.

## What's included

| Phase | What it adds | Key files |
|---|---|---|
| 1 | Text ReAct agent on a local Ollama model | `agent/graph.py`, `agent/llm.py`, `agent/main.py` |
| 2 | Wake word + speech-to-text + text-to-speech | `agent/voice/` |
| 3 | macOS app/UI control + browser control | `agent/computer/` |
| 4 | Semantic long-term memory + background daemon | `agent/memory.py`, `agent/daemon.py` |
| 5 | Optional escalation to a cloud model (Claude API) | `agent/llm.py` (`get_cloud_llm`), `ask_cloud_model` tool |
| — | Example MCP server | `agent/mcp_servers/` |

## Prerequisites

- macOS with Apple Silicon (M-series)
- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- A pulled local model, e.g. `ollama pull qwen2.5:7b`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Start Ollama if needed:

```bash
ollama serve
```

For browser control:

```bash
playwright install chromium
```

Grant Accessibility/Automation permissions in macOS System Settings when prompted.

## Run

```bash
python -m agent.main
python -m agent.main --voice
python -m agent.main --web
python -m agent.main --daemon
```

The web UI binds to `127.0.0.1:8765`.

## Safety

Real actions such as shell commands, file writes/deletes, app control, typing, and browser actions use a confirmation gate. Be especially careful with unattended voice and daemon modes; read-only tools are the safest starting point.

## Project layout

```text
agent/
  config.py
  graph.py
  llm.py
  main.py
  memory.py
  session.py
  safety.py
  tools.py
  daemon.py
  voice/
  computer/
  mcp_servers/
  webui/
tests/
requirements.txt
.env.example
.gitignore
```
