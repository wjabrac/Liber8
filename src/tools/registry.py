"""Tool Registry for Execution Gateway."""

from typing import Any, Callable, Dict, Optional


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        is_write: bool,
        is_network: bool,
        func: Callable,
        *,
        requires_isolation: bool = False,
    ) -> None:
        self._tools[name] = {
            "name": name,
            "is_write": is_write,
            "is_network": is_network,
            "requires_isolation": requires_isolation,
            "func": func,
        }

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        return self._tools.get(name)
