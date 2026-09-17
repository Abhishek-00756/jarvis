"""Guard generic file tools from sensitive macOS and credential paths."""

import os
from pathlib import Path

SENSITIVE_DIRS = {
    "~/.ssh", "~/.aws", "~/.azure", "~/.kube",
    "~/Library/Keychains",
}
SYSTEM_DIRS = {"/System", "/Library", "/private/etc", "/etc", "/var/root"}
SENSITIVE_BASENAMES = {
    ".env", ".netrc", ".npmrc", "credentials", "credentials.json",
    "id_rsa", "id_ed25519", "id_ecdsa",
}
SENSITIVE_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".pkcs12")


def _normalized(path: str) -> Path:
    return Path(os.path.expanduser(path)).resolve(strict=False)


def _is_within(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def check_path(path: str, operation: str = "read") -> tuple[bool, str]:
    """Return whether a generic file tool may access ``path``."""
    try:
        p = _normalized(path)
    except (OSError, RuntimeError):
        return False, f"Invalid path: {path}"

    for raw in SENSITIVE_DIRS:
        if _is_within(p, _normalized(raw)):
            return False, f"Access to sensitive path is blocked: {p}"

    for raw in SYSTEM_DIRS:
        if _is_within(p, _normalized(raw)):
            return False, f"Access to protected system path is blocked: {p}"

    name = p.name.lower()
    if name in SENSITIVE_BASENAMES:
        return False, f"Access to sensitive file is blocked: {p}"
    if name.startswith(".env.") and name != ".env.example":
        return False, f"Access to environment-secret file is blocked: {p}"
    if name.endswith(SENSITIVE_SUFFIXES):
        return False, f"Access to credential/key material is blocked: {p}"

    home = Path.home().resolve()
    if operation in {"write", "delete", "move", "copy", "rename", "create"} and p == home:
        return False, "The home directory itself cannot be replaced or deleted."
    return True, ""


def filter_visible_paths(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip() and check_path(line.strip(), "read")[0]]
