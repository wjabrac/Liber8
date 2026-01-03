"""Writeback agent for persisting memory blocks."""

from __future__ import annotations

from ..contracts import MemoryBlock, TagSet
from ..memory_adapter import FileSystemMemoryAdapter


def write_memory(synthesis: str, tags: TagSet, memory_adapter: FileSystemMemoryAdapter) -> str:
    memory_block = MemoryBlock(
        content=synthesis,
        tags=tags,
        provenance={"source": "router"},
        lane="episodic",
        confidence=0.6,
    )
    memory_adapter.write(memory_block)
    return memory_block.id
