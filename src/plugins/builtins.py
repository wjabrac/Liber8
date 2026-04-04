"""Built-in specialization plugins for LIBR8."""

from __future__ import annotations

from typing import List

from .contracts import PluginAttachment, PluginContext


def select_builtin_plugins(context: PluginContext) -> List[PluginAttachment]:
    task = context.task.lower()
    plugins: List[PluginAttachment] = []

    if any(word in task for word in ("plan", "strategy", "prioritize", "sequence")):
        plugins.append(
            PluginAttachment(
                name="planning_strategy",
                role="planning",
                heuristics=["favor decomposition", "surface tradeoffs", "preserve ordering constraints"],
                preferred_agents=["researcher", "synthesizer"],
            )
        )

    if any(word in task for word in ("code", "debug", "patch", "refactor", "python", "program", "tests")):
        plugins.append(
            PluginAttachment(
                name="programming",
                role="programming",
                domain_background=["codebase context", "tests", "local automation"],
                heuristics=["prefer deterministic tool use", "preserve repo invariants"],
                preferred_agents=["interpreter", "critic"],
            )
        )

    if any(word in task for word in ("research", "analyze", "compare", "investigate")):
        plugins.append(
            PluginAttachment(
                name="research",
                role="research",
                domain_background=["retrieval-heavy synthesis", "evidence collation"],
                heuristics=["favor broad retrieval", "preserve provenance"],
                preferred_agents=["researcher", "critic"],
            )
        )

    if any(word in task for word in ("tone", "charm", "friendly", "persuasive", "marketing", "copy", "brand")):
        plugins.append(
            PluginAttachment(
                name="tone_style",
                role="style",
                style_hints=["adapt tone to task-sensitive communication"],
                heuristics=["preserve factual core while shaping style"],
            )
        )

    if any(word in task for word in ("critique", "review", "validate", "check")):
        plugins.append(
            PluginAttachment(
                name="critique",
                role="critique",
                heuristics=["look for regressions", "prioritize correctness over presentation"],
                preferred_agents=["critic", "validator"],
            )
        )

    return plugins

