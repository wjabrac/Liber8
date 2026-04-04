"""Specialization plugin contracts for LIBR8."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PluginContext:
    task: str
    tags: Dict[str, Any]
    selected_agents: List[str]


@dataclass
class PluginAttachment:
    name: str
    role: str
    domain_background: List[str] = field(default_factory=list)
    style_hints: List[str] = field(default_factory=list)
    heuristics: List[str] = field(default_factory=list)
    preferred_agents: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "domain_background": self.domain_background,
            "style_hints": self.style_hints,
            "heuristics": self.heuristics,
            "preferred_agents": self.preferred_agents,
        }
