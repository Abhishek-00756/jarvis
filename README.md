# Jarvis — local-first autonomous Mac assistant

This project is a local-first personal assistant for macOS. The agent runs
against a local Ollama model by default and exposes tools for files, apps,
browser automation, Apple apps, messaging, system controls, voice, memory,
web search, and a small background daemon.

The current implementation is a strong Python agent foundation, not a
finished Siri replacement. High-impact interactive actions are gated by an
explicit confirmation flow; unattended daemon mode uses a physically
restricted read-only tool surface.

## What is implemented

- Local LangGraph tool-calling loop with self-correction.
- Persistent session history and long-term memory notes/facts.
- Finder/Spotlight file search, read/write/move/copy/rename/trash/archive.
- PDF, DOCX, PPTX and spreadsheet extraction/search.
- Mail, Calendar, Reminders, Notes and Contacts automation via AppleScript.
- WhatsApp and iMessage messaging plus WhatsApp call automation.
- Safari/Chrome active-tab context and a separate Playwright controlled browser.
- Browser tabs, navigation, scrolling, selectors, links and safe downloads.
- Screen capture + Apple Vision OCR from plain Python.
- macOS battery, CPU, memory, disk, network, volume, brightness and power controls.
- Background APScheduler/watchdog daemon with read-only isolation.
- LaunchAgent install/uninstall/status commands for login startup.
- Dynamic tool discovery that scopes the model to relevant tools on each request.

## Security model

### Shell command policy

`run_shell_command` is classified before any confirmation dialog:

- **Blocked**: root/system destruction, disk formatting, fork bombs, `sudo`,
  credential/keychain access, destructive git operations, and other known
  high-risk patterns.
- **Safe**: a narrow set of read-only commands, plus strictly read-only git
  forms such as `status`, `log`, `diff`, `show`, display-only `branch`, and
  display-only `remote` operations.
- **Review**: everything else requires explicit user confirmation.
- Shell pipes, redirects, chaining and substitutions are never pre-approved.
- Safe commands run without a shell; reviewed commands use explicit `/bin/zsh`
  after confirmation and a minimal sanitized environment.

This is policy hardening, not a kernel-level sandbox. A determined local
attacker could still route around pattern-based rules, so destructive actions
remain confirmation-gated rather than treated as impossible.

### Generic filesystem path policy

`agent/security/path_policy.py` prevents generic file tools from reading or
writing credential stores and sensitive macOS locations such as `.env` files,
SSH/AWS/Kubernetes credentials, Keychains, and system directories. Spotlight
results are filtered so protected paths are not returned through generic search.

### Prompt-injection boundary

Retrieved content is wrapped as `[UNTRUSTED EXTERNAL CONTENT]` and explicitly
marked as data rather than instructions. This covers files, documents, email,
notes, browser text, clipboard/context, screen OCR, application UI text, and
shell output. Common injection-like phrasing is logged without storing the
payload itself, and content is capped before it reaches the model.

### Cloud privacy boundary

Cloud escalation is opt-in. The cloud graph receives only the current user
request and a very small read-only tool surface; it does not receive the local
tool transcript, browser contents, email contents, clipboard, or memory by
default. Explicit `ask_cloud_model` calls are confirmation-gated.

### Unattended daemon isolation

Daemon mode uses `UNATTENDED_TOOLS`, not `ALL_TOOLS`. The daemon tool surface
contains read-only file/document/memory/task/time operations only, and automatic
cloud escalation is disabled. This is physical tool-surface isolation rather
than a prompt-only instruction.

## Screen OCR

`read_screen_text`, `find_text_on_screen`, and `get_screen_context` use macOS's
`screencapture` command and Apple's Vision framework through
`pyobjc-framework-Vision`. No Swift/Xcode app is required. Grant Screen
Recording permission to the terminal or IDE running Jarvis.

Temporary screenshots are unique per request and removed after OCR completes.
Do not use screen OCR while sensitive information is visible unless you intend
for the model to process it.

## Login at startup

Install the background daemon as a macOS LaunchAgent:

```bash
python -m agent.system.launch_agent install
python -m agent.system.launch_agent status
python -m agent.system.launch_agent uninstall
```

The generated plist uses `RunAtLoad` and `KeepAlive`, and logs to
`~/.jarvis_agent/logs/`.

## Browser control

The Playwright browser uses a persistent profile at
`~/.jarvis_agent/browser_profile/` so site logins survive restarts. Browser
downloads are stored under `~/.jarvis_agent/downloads/`; filenames are reduced
to a basename and existing downloads are not silently overwritten.

For "this" page/reel/file, the Context Engine checks the user's active
Safari/Chrome tab and clipboard first. Instagram-native reel sharing still
uses the controlled Playwright browser because the Instagram Share dialog is
automated there. WhatsApp/no-platform sharing can use the real Safari/Chrome
active URL.

## Dynamic tool discovery

Jarvis does not need to expose all interactive tools to the model on every
request. `agent/tool_router.py` uses deterministic category/keyword matching
to select a focused subset, normally capped at about 25 tools, while keeping
explicit cross-domain dependencies for requests such as "send this reel to
Rahul on WhatsApp".

When no category matches, Jarvis falls back to the full interactive registry
rather than guessing. Set `JARVIS_DYNAMIC_TOOLS=false` to disable routing while
debugging.

The router operates on the combined legacy + extended registry and does not
remove any tool from `ALL_TOOLS` or `EXTRA_TOOLS`.

## Email write-side

Mail tools now cover drafting and inbox management in addition to reading:
`draft_email`, `reply_email`, `forward_email`, `mark_email_read`,
`mark_email_unread`, and `archive_email`. Sending/replying/forwarding/archive
operations remain confirmation-gated; draft creation does not transmit mail.

## Remaining work

The bigger architectural pieces are intentionally separate from this pass:

- Native Swift/SwiftUI shell for a menu bar app, global hotkey, native settings,
  and App Intents/Siri.
- Configurable multi-tier action policy (read-only through destructive/admin)
  instead of the current per-tool confirmation set.
- General event bus/routine engine and full plan/preview/verify/undo workflow.
- Scoped file-operation undo before attempting any universal undo system.
- Advanced voice VAD, barge-in, noise/echo handling, and audio-device selection.
- A machine-generated dependency lock (`uv.lock`) and broader macOS integration
  testing once the runtime environment is available.

## Installation

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start Ollama separately:

```bash
ollama serve
```

For browser automation:

```bash
playwright install chromium
```

Grant Automation and Accessibility permissions as macOS prompts for them.
For OCR, grant Screen Recording permission. For voice, grant Microphone access.

## Run

```bash
python -m agent.main
python -m agent.main --voice
python -m agent.main --web
python -m agent.main --daemon
```

The web UI binds to `127.0.0.1` only.

## Project layout

```text
jarvis-agent/
├── agent/
│   ├── config.py
│   ├── graph.py
│   ├── llm.py
│   ├── main.py
│   ├── memory.py
│   ├── session.py
│   ├── safety.py
│   ├── tools.py
│   ├── tool_router.py
│   ├── daemon.py
│   ├── util.py
│   ├── computer/
│   │   ├── apple_apps.py
│   │   ├── browser_control.py
│   │   ├── finder_control.py
│   │   ├── macos_control.py
│   │   ├── media_control.py
│   │   ├── messaging.py
│   │   └── whatsapp_control.py
│   ├── context/
│   │   ├── context.py
│   │   ├── browser_context.py
│   │   ├── clipboard.py
│   │   └── screen.py
│   ├── documents/
│   │   └── extractor.py
│   ├── security/
│   │   ├── audit.py
│   │   ├── content_policy.py
│   │   ├── path_policy.py
│   │   ├── secrets.py
│   │   └── shell_policy.py
│   ├── system/
│   │   ├── system_control.py
│   │   └── launch_agent.py
│   ├── voice/
│   │   └── voice_loop.py (+ STT/TTS/wake-word helpers)
│   └── webui/
│       ├── server.py
│       └── static/index.html
├── tests/
│   ├── test_tools.py
│   ├── test_safety.py
│   └── test_tool_router.py
├── .github/workflows/ci.yml
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## Testing

The CI workflow performs an AST syntax check and validates that every
categorized router entry exists in the combined tool registry. A best-effort
full pytest run executes on a macOS runner because parts of Jarvis target
Apple-specific APIs and MLX.

Run locally with:

```bash
python -m pytest -q
```
