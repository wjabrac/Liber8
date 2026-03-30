"""Tool Policy enforcement for Execution Gateway."""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ToolPolicy:
    mode: str  # 'read_only' or 'write'
    network_allowed: bool
    path_allowlists: List[str]

    def can_execute(self, tool_name: str, is_write: bool, is_network: bool, path: Optional[str] = None) -> bool:
        if is_write and self.mode != "write":
            return False
        if is_network and not self.network_allowed:
            return False
            
        if path:
            # Simple prefix-based allowlisting for CX-011
            allowed = any(path.startswith(p) for p in self.path_allowlists)
            if not allowed:
                return False
                
        return True
