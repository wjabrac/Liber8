"""Execution gateway with approval gating and sandbox confinement."""

from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .classifier import classify_command


def execute_command(
    command: str,
    *,
    approval_token: Optional[str] = None,
    timeout: float = 10.0,
    sandbox_root: Optional[str] = None,
    working_directory: Optional[str] = None,
) -> Dict[str, Any]:
    classification = classify_command(command)
    approved = _is_approved(command, approval_token)
    allowed = classification in {"read_only", "write_non_destructive"} or approved

    if classification in {"destructive", "network"} and not approved:
        return {
            "command": command,
            "classification": classification,
            "approved": False,
            "allowed": False,
            "status": "blocked",
            "stdout": "",
            "stderr": f"Blocked {classification} command without approval token.",
            "exit_code": None,
            "duration": 0.0,
        }

    if not allowed:
        return {
            "command": command,
            "classification": classification,
            "approved": approved,
            "allowed": False,
            "status": "blocked",
            "stdout": "",
            "stderr": "Command not allowed without approval token.",
            "exit_code": None,
            "duration": 0.0,
        }

    sandbox = None
    cwd = None
    if sandbox_root is not None:
        sandbox = _resolve_existing_path(sandbox_root)
        if sandbox is None:
            return {
                "command": command,
                "classification": classification,
                "approved": approved,
                "allowed": False,
                "status": "blocked",
                "stdout": "",
                "stderr": "Sandbox root does not exist.",
                "exit_code": None,
                "duration": 0.0,
            }
        cwd = _resolve_working_directory(working_directory, sandbox)
        if cwd is None:
            return {
                "command": command,
                "classification": classification,
                "approved": approved,
                "allowed": False,
                "status": "blocked",
                "stdout": "",
                "stderr": "Working directory escapes sandbox.",
                "exit_code": None,
                "duration": 0.0,
            }
        outside_path = _command_references_outside_sandbox(command, sandbox, cwd)
        if outside_path is not None:
            return {
                "command": command,
                "classification": classification,
                "approved": approved,
                "allowed": False,
                "status": "blocked",
                "stdout": "",
                "stderr": f"Command references path outside sandbox: {outside_path}",
                "exit_code": None,
                "duration": 0.0,
            }
    elif working_directory is not None:
        cwd = Path(working_directory).resolve()

    start = time.monotonic()
    env = os.environ.copy()
    if sandbox is not None:
        env["LIBR8_SANDBOX_ROOT"] = str(sandbox)

    completed = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(cwd) if cwd is not None else None,
        env=env,
    )
    duration = time.monotonic() - start
    return {
        "command": command,
        "classification": classification,
        "approved": approved,
        "allowed": True,
        "status": "executed",
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "exit_code": completed.returncode,
        "duration": duration,
        "sandbox_root": str(sandbox) if sandbox is not None else None,
        "working_directory": str(cwd) if cwd is not None else None,
    }


def _normalize_command(command: str) -> str:
    return " ".join(command.strip().split())


def _is_approved(command: str, approval_token: Optional[str]) -> bool:
    if approval_token is None:
        return False
    prefix = "APPROVE:"
    if not approval_token.startswith(prefix):
        return False
    approved_command = approval_token[len(prefix) :].strip()
    return _normalize_command(approved_command) == _normalize_command(command)


def _resolve_existing_path(path_str: str) -> Optional[Path]:
    try:
        path = Path(path_str).resolve()
    except OSError:
        return None
    return path if path.exists() else None


def _resolve_working_directory(working_directory: Optional[str], sandbox: Path) -> Optional[Path]:
    if not working_directory:
        return sandbox
    candidate = Path(working_directory)
    resolved = candidate.resolve() if candidate.is_absolute() else (sandbox / candidate).resolve()
    return resolved if _is_within(resolved, sandbox) else None


def _command_references_outside_sandbox(command: str, sandbox: Path, cwd: Path) -> Optional[str]:
    for token in _extract_path_tokens(command):
        resolved = _resolve_token_path(token, sandbox, cwd)
        if resolved is not None and not _is_within(resolved, sandbox):
            return token
    return None


def _extract_path_tokens(command: str) -> list[str]:
    tokens = []
    for raw in re.findall(r'"[^"]+"|\'[^\']+\'|\S+', command):
        token = raw.strip().strip('"').strip("'")
        if _looks_like_path(token):
            tokens.append(token)
    for target in re.findall(r">>?\s*([^\s]+)", command):
        cleaned = target.strip().strip('"').strip("'")
        if cleaned and cleaned not in tokens:
            tokens.append(cleaned)
    return tokens


def _looks_like_path(token: str) -> bool:
    if not token or token.startswith("-"):
        return False
    if token.startswith((".", "~", "/", "\\")):
        return True
    if len(token) >= 3 and token[1] == ":" and token[0].isalpha():
        return True
    return "/" in token or "\\" in token


def _resolve_token_path(token: str, sandbox: Path, cwd: Path) -> Optional[Path]:
    candidate = Path(token)
    try:
        if candidate.is_absolute():
            return candidate.resolve()
        return (cwd / candidate).resolve()
    except OSError:
        return None


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
