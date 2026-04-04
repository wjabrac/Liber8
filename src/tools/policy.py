"""Tool Policy enforcement for Execution Gateway."""

from dataclasses import dataclass
from typing import List, Optional

from .paths import is_within_allowed_roots


@dataclass
class ToolPolicy:
    mode: str  # 'read_only' or 'write'
    network_allowed: bool
    path_allowlists: List[str]
    enforce_isolation_for_writes: bool = False

    def can_execute(self, tool_name: str, is_write: bool, is_network: bool, path: Optional[str] = None) -> bool:
        if is_write and self.mode != "write":
            return False
        if is_network and not self.network_allowed:
            return False

        if path and self.path_allowlists and not is_within_allowed_roots(path, self.path_allowlists):
            return False

        return True
