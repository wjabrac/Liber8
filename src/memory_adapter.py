"""Filesystem-backed memory adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .contracts import MemoryBlock, QueryPlan, TagSet


class FileSystemMemoryAdapter:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.last_query_plan: Optional[QueryPlan] = None

    def read(self, tags: TagSet, query_plan: Optional[QueryPlan] = None) -> List[MemoryBlock]:
        self.last_query_plan = query_plan
        if not self.path.exists():
            return []

        blocks: List[MemoryBlock] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    blocks.append(MemoryBlock.from_dict(json.loads(line)))

        filtered = blocks if not tags.tags else [block for block in blocks if _tags_overlap(block.tags, tags)]
        if query_plan is not None:
            lane_filter = query_plan.filters.get("lane") if isinstance(query_plan.filters, dict) else None
            lane_filters = query_plan.filters.get("lanes") if isinstance(query_plan.filters, dict) else None
            if lane_filter:
                filtered = [block for block in filtered if block.lane == lane_filter]
            if lane_filters:
                filtered = [block for block in filtered if block.lane in lane_filters]
            return filtered[: query_plan.limits]
        return filtered

    def write(self, block: MemoryBlock) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(block.to_dict()))
            handle.write("\n")


def _tags_overlap(left: TagSet, right: TagSet) -> bool:
    for key, value in left.tags.items():
        if key in right.tags and right.tags[key] == value:
            return True
    return False
