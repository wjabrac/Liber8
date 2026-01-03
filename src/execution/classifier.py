"""Command classification helpers."""

from __future__ import annotations

import os
import re
import shlex
from pathlib import Path


READ_ONLY_COMMANDS = {"ls", "dir", "cat", "type"}
WRITE_NON_DESTRUCTIVE = {"mkdir", "touch"}
DESTRUCTIVE_COMMANDS = {
    "rm",
    "del",
    "rmdir",
    "remove-item",
    "format",
    "diskpart",
    "shutdown",
    "reboot",
    "stop-service",
    "uninstall",
}
NETWORK_COMMANDS = {"curl", "wget", "invoke-webrequest"}


def classify_command(command: str) -> str:
    cleaned = command.strip()
    if not cleaned:
        return "destructive"
    lower = cleaned.lower()
    tokens = _tokenize(lower)
    if not tokens:
        return "destructive"

    base = tokens[0]
    if _is_network_command(base, tokens):
        return "network"
    if _is_destructive_command(base, tokens, cleaned):
        return "destructive"
    if _is_read_only_command(base, tokens):
        return "read_only"
    if base in WRITE_NON_DESTRUCTIVE:
        return "write_non_destructive"
    if _has_safe_redirect(cleaned):
        return "write_non_destructive"
    return "destructive"


def _tokenize(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def _is_network_command(base: str, tokens: list[str]) -> bool:
    if base in NETWORK_COMMANDS:
        return True
    if base == "pip" and "install" in tokens:
        return True
    if base == "npm" and "install" in tokens:
        return True
    return False


def _is_destructive_command(base: str, tokens: list[str], command: str) -> bool:
    if base in DESTRUCTIVE_COMMANDS:
        return True
    if base == "git" and ("reset" in tokens and "--hard" in tokens):
        return True
    if base == "git" and ("clean" in tokens and "-fdx" in tokens):
        return True
    return _has_overwrite_redirect(command)


def _is_read_only_command(base: str, tokens: list[str]) -> bool:
    if base in READ_ONLY_COMMANDS:
        return True
    if base == "git" and ("status" in tokens or "diff" in tokens):
        return True
    if base in {"python", "python3"}:
        if "-m" in tokens and "unittest" in tokens:
            return True
        if "-c" in tokens:
            return True
    return False


def _has_overwrite_redirect(command: str) -> bool:
    if ">" not in command:
        return False
    if ">>" in command:
        return False
    targets = re.findall(r">\s*([^\s]+)", command)
    if not targets:
        return True
    for target in targets:
        path = Path(target.strip().strip('"').strip("'"))
        if path.exists() and not _is_temp_path(path):
            return True
    return False


def _has_safe_redirect(command: str) -> bool:
    if ">" not in command:
        return False
    if ">>" in command:
        return False
    targets = re.findall(r">\s*([^\s]+)", command)
    if not targets:
        return False
    for target in targets:
        path = Path(target.strip().strip('"').strip("'"))
        if _is_temp_path(path) and not path.exists():
            return True
    return False


def _is_temp_path(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    tmp_roots = {Path("/tmp"), Path("/var/tmp"), Path(os.getenv("TMPDIR", "/tmp"))}
    return any(str(resolved).startswith(str(root)) for root in tmp_roots)
