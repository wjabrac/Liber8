"""Execution gateway with approval gating."""

from __future__ import annotations

import subprocess
import time
from typing import Any, Dict, Optional

from .classifier import classify_command


def execute_command(
    command: str,
    *,
    approval_token: Optional[str] = None,
    timeout: float = 10.0,
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

    start = time.monotonic()
    completed = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
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
