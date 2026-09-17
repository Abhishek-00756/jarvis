"""Conservative policy for Jarvis shell execution."""

import os
import re
import shlex
from pathlib import Path

ALLOWLIST_COMMANDS = {
    "ls", "cat", "pwd", "echo", "whoami", "date", "grep", "find", "wc",
    "head", "tail", "df", "du", "ps", "top", "uname", "which", "file",
}
READ_ONLY_GIT = {"status", "log", "diff", "show"}
READ_ONLY_GIT_BRANCH = {"-a", "-r", "-v", "-vv", "--all", "--remotes", "--verbose"}
READ_ONLY_GIT_REMOTE = {"-v", "--verbose", "show", "get-url"}
COMPOSITION = [r";", r"\|\|", r"&&", r"\|", r">>", r">", r"<", r"`", r"\$\(", r"\$\{"]
BLOCKED = [
    r"rm\s+(?:-[^\s]+\s+)*-r[^\s]*\s+/(\s|$)",
    r"rm\s+(?:-[^\s]+\s+)*-r[^\s]*\s+~/?\s*$",
    r"\bmkfs(?:\.|\s|$)", r"\bdd\s+if=.*of=/dev/",
    r":\(\)\s*\{\s*:\|:&\s*\}\s*;\s*:",
    r"\bshutdown\b", r"\breboot\b", r"\bhalt\b",
    r"launchctl\s+(?:unload|remove|bootout)\b.*\.plist",
    r"security\s+dump-keychain", r"security\s+find-generic-password.*-w",
    r"curl\s+.*\|\s*(?:ba)?sh\b", r"wget\s+.*\|\s*(?:ba)?sh\b",
    r">\s*/dev/(?:disk|sd|rdisk)", r"chmod\s+-R\s+777\s+/",
    r"\bgit\s+push\s+.*(?:--force\b|-f\b)",
    r"\bgit\s+push\s+.*--force-with-lease\b",
    r"\bgit\s+clean\s+.*(?:-[a-z]*f[a-z]*\b|--force\b)",
    r"\bgit\s+reset\s+.*--hard\b", r"\bgit\s+rebase\b",
    r"\bgit\s+checkout\s+--\s+\.", r"\bgit\s+restore\s+.*--source\b",
]
SENSITIVE = [
    r"(?:~|/Users/[^\s/]+)/(?:\.ssh|\.aws|\.azure|\.kube)(?:/|\s|$)",
    r"(?:~|/Users/[^\s/]+)/Library/Keychains(?:/|\s|$)",
    r"(?:^|\s)(?:/private)?/etc(?:/|\s|$)", r"(?:^|\s)/var/root(?:/|\s|$)",
    r"(?:^|\s)(?:~|/Users/[^\s/]+)/\.env(?!\.example)(?:\.[^\s/]+)?(?:\s|$)",
    r"\b(?:id_rsa|id_ed25519|id_ecdsa)\b",
]


def _tokens(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def _composition(command: str) -> bool:
    return any(re.search(p, command) for p in COMPOSITION)


def _home_root(command: str) -> bool:
    if not re.search(r"\b(rm|mv|cp|chmod|chown|truncate|tee)\b", command):
        return False
    home = Path.home().resolve()
    for token in _tokens(command):
        if token.startswith("-"):
            continue
        try:
            if Path(token).expanduser().resolve(strict=False) == home:
                return True
        except (OSError, RuntimeError):
            pass
    return False


def classify_command(command: str) -> tuple[str, str]:
    """Return ``blocked``, ``safe`` or ``review`` plus a reason."""
    if not isinstance(command, str) or not command.strip():
        return "blocked", "Empty shell command."
    if "\x00" in command:
        return "blocked", "NUL bytes are not permitted."
    if len(command) > 4000:
        return "blocked", "Shell command exceeds the 4000-character limit."
    if any(re.search(p, command, re.IGNORECASE) for p in BLOCKED):
        return "blocked", "Matches a blocked high-risk shell pattern."
    if "sudo" in _tokens(command):
        return "blocked", "sudo is not permitted."
    if _home_root(command):
        return "blocked", "Command targets the home directory itself."
    if any(re.search(p, command, re.IGNORECASE) for p in SENSITIVE):
        return "blocked", "Command attempts to access protected credential or system data."
    if _composition(command):
        return "review", "Shell composition requires confirmation."
    tokens = _tokens(command)
    if not tokens:
        return "blocked", "Empty shell command."
    if tokens[0] == "git":
        if len(tokens) < 2:
            return "review", "git requires a subcommand."
        sub, args = tokens[1], tokens[2:]
        if sub == "branch" and "-D" in args:
            return "blocked", "Destructive git branch deletion (-D) is not permitted."
        if sub in READ_ONLY_GIT:
            return "safe", f"git {sub} is read-only."
        if sub == "branch" and (not args or all(a in READ_ONLY_GIT_BRANCH or a.startswith("-") for a in args)):
            mutating = {"-d", "-D", "--delete", "-m", "-M", "--move", "-c", "-C", "--copy"}
            if not any(a in mutating for a in args):
                return "safe", "git branch display operation is read-only."
        if sub == "remote" and (not args or args[0] in READ_ONLY_GIT_REMOTE):
            if not args or args[0] in {"-v", "--verbose", "show", "get-url"}:
                return "safe", "git remote display operation is read-only."
        return "review", f"git {sub} is not on the read-only list."
    if tokens[0] in ALLOWLIST_COMMANDS:
        return "safe", f"'{tokens[0]}' is on the read-only allowlist."
    return "review", "Not blocked and not pre-approved; needs explicit confirmation."


def sanitized_env() -> dict[str, str]:
    keep = {"PATH", "HOME", "USER", "SHELL", "LANG", "LC_ALL"}
    env = {k: v for k, v in os.environ.items() if k in keep}
    env["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/opt/homebrew/sbin"
    env.setdefault("HOME", str(Path.home()))
    env.setdefault("SHELL", "/bin/zsh")
    return env
