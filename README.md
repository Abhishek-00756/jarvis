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
| 4 | Semantic long-term memory + background daemon | `agent/memory.py`, `agent/daemon.py` |
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
│   │   └── browser_control.py       # Playwright browser control
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

For sites with unstable/obfuscated UI element names (Instagram is the
main example — its nav uses auto-generated class names that change often
specifically to resist automation), prefer `browser_go_to("instagram_reels")`
over clicking through the nav with `browser_click`. It jumps straight to
the known URL instead of trying to find and click a fragile element. Add
more named shortcuts to `DIRECT_URLS` in `agent/computer/browser_control.py`
as you need them.

One thing outside this project's control: some sites (Instagram included)
run bot-detection and may occasionally show a login checkpoint or CAPTCHA
to an automated browser even with valid cookies. If that happens, it needs
a human to clear it once — there's no reliable way around that from code.

## "Send this to X" — sharing what's on screen

Two sharing paths exist, and the agent picks based on how you phrase it:

- **"Send this reel on Instagram"** → `share_reel_to_instagram_dm` — uses
  Instagram's own Share button and DM search, entirely within Instagram.
  This is Playwright-based (clicking real page elements by their
  accessible name/role, not raw CSS classes), which is meaningfully more
  stable than the WhatsApp Accessibility-API automation — but Instagram's
  button labels can still shift over time. If it can't find something, run
  `browser_inspect_page()` to see the current accessible names and update
  `SHARE_BUTTON_NAMES` / `SEND_BUTTON_NAMES` in `browser_control.py`.
- **"Send this reel on WhatsApp" / no platform specified** →
  `browser_get_current_url` + `whatsapp_send_message` — copies the link
  and sends it as a WhatsApp message instead.

**The catch, either way**: it only knows "this reel" if you're browsing
through *the agent's own controlled browser window* (the persistent
Playwright profile), not your everyday Safari/Chrome. If you're scrolling
reels in your normal browser, it has no visibility into that and will say
so rather than guess.

## WhatsApp calling — read this before relying on it

`whatsapp_call("contact name")` opens a chat via WhatsApp's search and
tries to click the voice/video call button. **This is UI automation, not
an official API** — WhatsApp Desktop has no AppleScript dictionary, so
it works by driving the Accessibility tree through System Events, the
same technique real Mac computer-use agents use. That means:

- It needs Accessibility permission granted to your terminal/VS Code.
- The exact call-button label can differ by WhatsApp version/locale. It
  tries a few common labels (`agent/computer/whatsapp_control.py`,
  `CALL_BUTTON_CANDIDATES`); if none match, it says so explicitly rather
  than pretending it worked.
- **If it can't find the button on your install**: ask the agent to
  "inspect the WhatsApp UI" (the `inspect_app_ui` tool), which dumps the
  actual Accessibility element names. Find the real call button's label
  in that output and add it to `CALL_BUTTON_CANDIDATES` /
  `VIDEO_BUTTON_CANDIDATES` in `whatsapp_control.py`.

This calibrate-once-then-it-works pattern is normal for Accessibility-API
automation on apps without a real API — it's the same reason a website
redesign can break a browser-automation script until you update a
selector.

## Extending further

- **Split more tools into MCP servers**: copy `filesystem_server.py`'s
  pattern for browser or macOS control, so other MCP clients (Claude Code,
  Claude Desktop) can share the same tools.
- **Swap the confirmation prompt**: replace the `input()` call in
  `safety.py` with a native macOS notification/approval dialog for a more
  Jarvis-like feel — keep the same function signature.
- **Tighten the escalation trigger**: right now cloud fallback only kicks
  in after `MAX_ITERATIONS` is hit. You could also add an explicit "ask the
  cloud" voice command, which the `ask_cloud_model` tool already supports.
- **Add more proactive daemon triggers**: calendar events (EventKit),
  Mail (AppleScript), or a Screen Time-style usage nudge are natural next
  additions in `agent/daemon.py`.
