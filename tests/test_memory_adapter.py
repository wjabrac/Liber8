import tempfile
import unittest
from pathlib import Path

from src.contracts import MemoryBlock, QueryPlan, TagSet
from src.memory_adapter import FileSystemMemoryAdapter


class TestFileSystemMemoryAdapter(unittest.TestCase):
    def test_read_filters_by_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = FileSystemMemoryAdapter(Path(tmpdir) / "memory.jsonl")
            adapter.write(
                MemoryBlock(
                    content="match",
                    tags=TagSet(schema_version="v0", tags={"intent": "match"}),
                    provenance={"source": "test"},
                    lane="episodic",
                    confidence=0.5,
                )
            )
            adapter.write(
                MemoryBlock(
                    content="miss",
                    tags=TagSet(schema_version="v0", tags={"intent": "miss"}),
                    provenance={"source": "test"},
                    lane="episodic",
                    confidence=0.5,
                )
            )
            results = adapter.read(TagSet(schema_version="v0", tags={"intent": "match"}))
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].content, "match")

    def test_query_plan_limits_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = FileSystemMemoryAdapter(Path(tmpdir) / "memory.jsonl")
            for idx in range(3):
                adapter.write(
                    MemoryBlock(
                        content=f"entry-{idx}",
                        tags=TagSet(schema_version="v0", tags={}),
                        provenance={"source": "test"},
                        lane="episodic",
                        confidence=0.5,
                    )
                )
            plan = QueryPlan(filters={}, limits=1, recency_bias=0.0)
            results = adapter.read(TagSet(schema_version="v0", tags={}), query_plan=plan)
            self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
