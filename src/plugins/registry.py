"""Plugin registry and selection helpers."""

from __future__ import annotations

from typing import List

from .builtins import select_builtin_plugins
from .contracts import PluginAttachment, PluginContext


class PluginRegistry:
    def select(self, context: PluginContext) -> List[PluginAttachment]:
        return select_builtin_plugins(context)
