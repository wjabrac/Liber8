"""Shared helpers for resolved-path policy checks."""

from __future__ import annotations

import os
from typing import Iterable


def resolve_boundary_path(path: str | os.PathLike[str]) -> str:
    """Resolve a path for policy evaluation and tool execution."""
    return os.path.realpath(os.path.abspath(os.fspath(path)))


def is_within_allowed_roots(
    path: str | os.PathLike[str],
    allowed_roots: Iterable[str | os.PathLike[str]],
) -> bool:
    """Return True when the resolved path is contained by any allowed root."""
    resolved_path = resolve_boundary_path(path)
    for root in allowed_roots:
        resolved_root = resolve_boundary_path(root)
        try:
            if os.path.commonpath([resolved_path, resolved_root]) == resolved_root:
                return True
        except ValueError:
            continue
    return False
