"""Synthesis agent for composing responses."""

from __future__ import annotations

from typing import List, Tuple

from ..contracts import MemoryBlock, TagSet, WritebackPackage


def synthesize(task: str, tags: TagSet, retrieved: List[MemoryBlock]) -> Tuple[str, WritebackPackage]:
    synthesis = f"SYNTHESIS: {task} (retrieved {len(retrieved)} memories)"
    writeback = WritebackPackage(
        episode=synthesis,
        distilled_facts=[task],
        procedural_snippet=None,
        tags=tags,
        evaluation_outcome="ok",
        promotion_notes="stored in episodic lane",
        demotion_notes=None,
    )
    return synthesis, writeback
