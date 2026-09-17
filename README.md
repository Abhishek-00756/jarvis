# Jarvis Agent — Complete Local Assistant

A local-first autonomous agent for macOS (Apple Silicon), built in five
layers: text reasoning core, voice I/O, computer/browser control, long-term
memory + background autonomy, and optional cloud fallback for hard
reasoning. Everything runs on your Mac by default; nothing leaves the
machine unless you explicitly configure cloud fallback or web search.

## What's included

| Phase | What it adds | Key files |
|---|---|---|
| 1 | Text ReAct agent on a local Ollama model | `agent/graph.py`, `agent/llm.py`, `agent/main.py` |
| 2 | Wake word + speech-to-text + text-to-speech | `agent/voice/` |
| 3 | macOS app/UI control + browser control | `agent/computer/` |
| 4 | Semantic long-term memory + background autonomy | `agent/memory.py`, `agent/daemon.py` |
| 5 | Optional escalation to a cloud model (Claude API) | `agent/llm.py` (`get_cloud_llm`), `ask_cloud_model` tool |
| — | Example MCP server (tool-sharing across clients) | `agent/mcp_servers/` |

## Prerequisites

- macOS with Apple Silicon (M-series)
- Python 3.11+
- [Ollama](https://ollama.ai) installed and running (`brew install ollama`)
- A pulled local model:
  ```bash
  ollama pull qwen2.5:7b      # good fit for 16GB RAM; use :14b (24-32GB) or :32b (48GB+) if you have more
  ```

## Setup

```bash
cd jarvis-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # then edit .env as needed
```

Start Ollama in another terminal if it isn't already running:
```bash
ollama serve
```

### If you want voice (Phase 2)

Voice deps (`openwakeword`, `mlx-whisper`, `kokoro-onnx`, `sounddevice`) are
already in `requirements.txt`. First run of `mlx-whisper` and `kokoro-onnx`
will download their model weights automatically. Grant Microphone access
when macOS prompts you.

### If you want computer/browser control (Phase 3)

```bash
playwright install chromium
```
Also grant your terminal (or VS Code, if you run it from there) **Accessibility**
and **Automation** permissions in System Settings > Privacy & Security —
macOS will prompt the first time a script tries to control another app.

### If you want cloud fallback (Phase 5)

Add your key to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```
Leave it blank to stay 100% local — the agent works fully without it and
just won't have an escalation path for tasks the local model can't resolve.

### If you want real web search

Add a [Tavily](https://tavily.com) key to `.env`:
```
TAVILY_API_KEY=tvly-...
```
Without it, `web_search` returns a clear placeholder instead of failing.

## Run

```bash
# Interactive text mode
python -m agent.main

# Hands-free voice mode
python -m agent.main --voice

# Animated browser chat UI (open http://127.0.0.1:8765)
python -m agent.main --web

# Background autonomous daemon (scheduled + filesystem triggers)
python -m agent.main --daemon
```

Type `exit` / `quit` in text mode, or say "stop" in voice mode, to end a
session. Ctrl+C stops the daemon or web server.

### About the web UI

`--web` starts a small local FastAPI server (nothing leaves your machine —
it's bound to 127.0.0.1) and opens a chat page with an animated status orb:

- **idle** — soft breathing pulse, waiting for input
- **thinking** — faster spin while the agent reasons/calls tools
- **speaking** — pulses while it talks back

Spoken replies use your browser's built-in text-to-speech (Web Speech API)
for zero extra setup. If you'd rather it use the same offline Kokoro voice
as `--voice` mode, swap the `speak()` function in
`agent/webui/static/index.html` to call a small `/speak` endpoint that
runs `agent/voice/tts.py` server-side instead.

## Project layout

```
jarvis-agent/
├── agent/
│   ├── config.py            # all settings (model, safety, voice, cloud)
│   ├── graph.py              # LangGraph ReAct loop + cloud escalation
│   ├── llm.py                # local (Ollama) + cloud (Claude) model access
│   ├── main.py                # CLI entry point (text / voice / daemon)
│   ├── memory.py              # flat facts + semantic notes (Chroma)
│   ├── session.py              # persistent conversation history + summarization
│   ├── safety.py               # confirmation gate for impactful actions
│   ├── tools.py                # all tool definitions, registered in ALL_TOOLS
│   ├── daemon.py                 # background/proactive autonomy loop
│   ├── voice/
│   │   ├── wake_word.py          # openWakeWord listener
│   │   ├── stt.py                 # MLX-Whisper transcription
│   │   ├── tts.py                  # Kokoro speech synthesis
│   │   └── voice_loop.py           # wires wake -> STT -> agent -> TTS
│   ├── computer/
│   │   ├── macos_control.py       # AppleScript/System Events app+UI control
│   │   ├── whatsapp_control.py     # WhatsApp call automation (Accessibility API)
│   │   ├── apple_apps.py           # Mail/Calendar/Reminders/Notes (AppleScript)
│   │   ├── finder_control.py        # expanded file management (find/move/trash/compress)
│   │   ├── media_control.py          # Music.app playback control
│   │   ├── messaging.py               # unified send_message() over WhatsApp/iMessage
│   │   └── browser_control.py       # Playwright browser control
│   ├── context/
│   │   ├── context.py               # get_current_context() — the top-level snapshot
│   │   ├── browser_context.py        # reads YOUR real Safari/Chrome active tab
│   │   └── clipboard.py               # pbcopy/pbpaste wrapper
│   ├── security/
│   │   ├── audit.py                   # structured action log
│   │   └── secrets.py                  # Keychain-backed credential storage
│   ├── system/
│   │   └── system_control.py           # battery/volume/network/power actions
│   ├── documents/
│   │   └── extractor.py                # PDF/DOCX/PPTX/spreadsheet reading
│   ├── tasks.py                          # simple persistent task manager
│   ├── mcp_servers/
│   │   └── filesystem_server.py  # example standalone MCP server
│   └── webui/
│       ├── server.py              # FastAPI backend for the chat UI
│       └── static/index.html       # animated orb + chat frontend
├── tests/
│   ├── test_tools.py
│   └── test_safety.py
├── requirements.txt
├── .env.example
└── README.md
```

## Safety model — read this before enabling voice/daemon mode

Every tool that takes a real action (shell commands, file writes/deletes,
app control, typing, browser navigation/clicks) is registered in
`config.CONFIRM_REQUIRED_TOOLS` and routes through `safety.confirm_action()`
before running. In text mode this is a blocking `y/N` prompt.

**In voice and daemon mode there's no one at a keyboard to answer that
prompt.** Before relying on either:
1. Decide which tools are safe to leave ungated for unattended use (read-only
   ones — `list_files`, `read_file`, `get_frontmost_app`, `browser_get_text`,
   `recall_fact`/`recall_notes` — are the safest starting set).
2. For daemon mode especially, consider removing destructive tools from
   `ALL_TOOLS` entirely rather than trusting a prompt that nothing is there
   to answer — an unanswered `input()` call will just hang, not fail safe.
3. Keep `DAEMON_LOG_PATH` (`~/.jarvis_agent/daemon.log`) and review it
   regularly while you build trust in the system.

## Autonomy upgrades in this version

### Persistent memory across sessions

Conversation history now survives restarts (`agent/session.py`), saved to
`~/.jarvis_agent/memory/session_history.json` after every turn in both text
mode and the web UI:

- **Text mode** loads it automatically on startup and tells you how many
  messages it resumed with.
- **Web UI** loads it via a `/history` endpoint when the page opens, so
  refreshing the browser doesn't lose the conversation.
- Once history passes 40 messages, the oldest are summarized (by the local
  model) into a long-term memory note and dropped from the active context,
  so it doesn't grow forever or blow past the model's context window.
- Voice mode doesn't use this yet — it's stateless per run. Wire it in the
  same way (`session.load_history()` / `session.maybe_summarize()` /
  `session.save_history()`) if you want that too.

### Self-correction

`MAX_ITERATIONS` was raised from 8 to 12, and the system prompt
(`agent/graph.py`) now explicitly instructs the agent to read a tool's
error, try an alternate approach (different tool, corrected argument, or a
diagnostic like `inspect_app_ui`), and retry before reporting failure. This
isn't a separate code path — it works because every tool already returns
its errors as plain text the model can read and react to; the prompt just
makes "try to recover" the expected behavior instead of "report and stop."

### App automation (Mail, Calendar, Reminders, Notes)

`agent/computer/apple_apps.py` — the most reliable automations in the
project, because Apple's own apps expose real AppleScript dictionaries
(no Accessibility-tree guesswork like WhatsApp needs):

- `send_email(to, subject, body)`
- `get_calendar_events_today()` — read-only, no confirmation needed
- `add_calendar_event(title, start_date_str, end_date_str, calendar_name)`
- `add_reminder(text, list_name, due_date_str)`
- `add_note(title, body)`

Date arguments must be in a format AppleScript's `date` coercion accepts,
e.g. `"1/5/2026 3:00:00 PM"`. All write actions require confirmation like
everything else destructive in this project.

## Browser control — logins and reliable navigation

The browser uses a **persistent profile** (`~/.jarvis_agent/browser_profile`),
so once you log into a site (Instagram, etc.) in the window it opens, that
login is remembered on later runs — you won't need to log in every time.

For sites with unreliable navigation, use the named `browser_go_to` shortcuts
such as `instagram_reels`, `instagram_home`, or `instagram_dms`.

## Context awareness

This version adds three capabilities that close a big chunk of the “what am I
doing right now?” gap:

- `get_current_context()` — combines frontmost app + active browser tab +
  clipboard into one snapshot.
- `get_active_browser_tab()` — reads the **user's real Safari or Chrome**
  frontmost tab via AppleScript, separate from Jarvis's controlled Playwright
  browser.
- `get_clipboard()` / `set_clipboard()` — lets Jarvis read or replace the system
  clipboard through `pbpaste` / `pbcopy`.

The screenshot/OCR layer is still intentionally left as a future addition;
ScreenCaptureKit/Vision would require a native helper and separate Screen
Recording permission on macOS.

## System controls

New `agent/system/system_control.py` exposes battery, disk, network, volume,
CPU, memory, uptime, timezone, brightness, and power actions. Power actions
(lock/sleep/restart/shutdown) and volume/brightness changes are gated through
the same confirmation policy.

## Finder / file management

`agent/computer/finder_control.py` adds safe-ish, purpose-specific tools over
Finder and macOS file utilities: recursive file search, recent files,
metadata, move/copy/rename, folder creation, trashing, revealing/opening,
and archive compression/extraction. Destructive actions use the confirmation
gate.

## Documents

`agent/documents/extractor.py` can read PDF, DOCX, PPTX, XLSX/XLSM/ODS-ish
(spreadsheet via `openpyxl`) content and search within PDFs. Results are
truncated so large documents don't explode the context window.

## Tasks + audit log

`agent/tasks.py` is a tiny persistent task store at `~/.jarvis_agent/tasks.json`
with create/list/complete/delete. `agent/security/audit.py` records structured
success/denial/failure information for tool actions, and `what_did_you_do_today`
exposes a human-readable recent-actions summary to the agent.

## Keychain-backed secrets

`agent/security/secrets.py` uses macOS `security` CLI Keychain lookups when
available, while keeping `.env` as the explicit development fallback. The
code never stores the secret value in the audit log.

## Cloud safety boundary

The cloud fallback is now **off by default** (`JARVIS_CLOUD_AUTO_ESCALATE=false`)
and the Claude model is bound only to `SAFE_CLOUD_TOOLS` — read-only/low-risk
operations. It cannot run your shell, delete files, send messages, or invoke
power actions. For sensitive tasks, prefer the fully local path. The default
cloud model is `claude-sonnet-5`; set `JARVIS_CLOUD_FALLBACK_MODEL` in `.env` to
change it.

## Known gaps / next additions

These are deliberate next steps rather than silently pretending they are done:

- **Native screen capture + OCR** (ScreenCaptureKit + Vision helper).
- **Global macOS hotkey** to invoke Jarvis without the terminal focused.
- **Native menu-bar app / approval UI** instead of CLI `input()` confirmation.
- **Event-driven automations** beyond the current morning schedule + file
  watcher (battery low, email received, calendar soon, clipboard changed, etc.).
- **Full Calendar/Reminder/Notes/Mail editing/search** beyond the current
  useful read/create subset.
- **Swift `SMAppService` / Login Item packaging** so Jarvis starts with macOS
  rather than a terminal command.
- **Streaming/cancellation in the web UI**.
- **Model routing** (small fast local model vs bigger reasoning/vision model).
- **Voice persistence + barge-in / VAD**.
- **Prompt-injection hardening** for external web/document content.
- **MCP v2 migration** when you deliberately upgrade the SDK.

This repository is intended as a strong local-agent foundation rather than a
finished Siri replacement. Build permissions and autonomy gradually.
