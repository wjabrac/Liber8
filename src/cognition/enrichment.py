"""Enrichment selection for LIBR8 runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.plugins.contracts import PluginAttachment


@dataclass
class EnrichmentBundle:
    sources: List[str] = field(default_factory=list)
    procedural_snippets: List[str] = field(default_factory=list)
    plugin_hints: List[Dict[str, Any]] = field(default_factory=list)
    role_models: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sources": self.sources,
            "procedural_snippets": self.procedural_snippets,
            "plugin_hints": self.plugin_hints,
            "role_models": self.role_models,
        }


def select_enrichment(
    task: str,
    tags: Dict[str, Any],
    plugins: List[PluginAttachment],
    selected_agents: List[str],
    role_models: Dict[str, str],
) -> EnrichmentBundle:
    sources = ["prior_memory", "run_state"]
    if selected_agents:
        sources.append("agent_plan")
    if any(plugin.role == "programming" for plugin in plugins):
        sources.extend(["codebase_files", "test_suite"])
    if any(plugin.role == "research" for plugin in plugins):
        sources.extend(["retrieved_documents", "prior_conversations"])
    if any(plugin.role == "style" for plugin in plugins):
        sources.append("style_guides")

    procedural_snippets: List[str] = []
    if "intent" in tags:
        procedural_snippets.append(f"intent:{tags['intent']}")
    if any(word in task.lower() for word in ("repeat", "again", "routine", "macro")):
        procedural_snippets.append("favor procedural reuse")

    return EnrichmentBundle(
        sources=sources,
        procedural_snippets=procedural_snippets,
        plugin_hints=[plugin.to_dict() for plugin in plugins],
        role_models=role_models,
    )
