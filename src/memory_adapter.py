"""Filesystem-backed memory adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .contracts import MemoryBlock, TagSet


class FileSystemMemoryAdapter:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read(self, tags: TagSet, query_plan: Optional[object] = None) -> List[MemoryBlock]:
        _ = query_plan
        if not self.path.exists():
            return []
        blocks: List[MemoryBlock] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    blocks.append(MemoryBlock.from_dict(json.loads(line)))
        if not tags.tags:
            return blocks
        return [block for block in blocks if _tags_overlap(block.tags, tags)]

    def write(self, block: MemoryBlock) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(block.to_dict()))
            handle.write("\n")


def _tags_overlap(left: TagSet, right: TagSet) -> bool:
    for key, value in left.tags.items():
        if key in right.tags and right.tags[key] == value:
            return True
    return False
