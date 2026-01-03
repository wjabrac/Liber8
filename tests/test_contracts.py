import json
import unittest

from src.contracts import (
    EventRecord,
    MemoryBlock,
    QueryPlan,
    TagSet,
    WritebackPackage,
)


class ContractsTest(unittest.TestCase):
    def test_event_record_json_roundtrip(self) -> None:
        tags = TagSet(schema_version="v0", tags={"intent": "test"}, uncertainty={"intent": 0.1})
        query_plan = QueryPlan(filters={"intent": "test"}, limits=1, recency_bias=0.5)
        event = EventRecord(
            task="demo",
            tags=tags,
            query_plan=query_plan,
            retrieved_ids=[],
            actions=["tag_extraction"],
            tool_calls=[{"name": "tagger"}],
            validations=["contracts_v0"],
            outcome="success",
            provenance={"source": "unit_test"},
        )
        payload = event.to_dict()
        json.dumps(payload)
        rehydrated = EventRecord.from_dict(payload)
        self.assertEqual(rehydrated.task, "demo")

    def test_memory_block_validation(self) -> None:
        tags = TagSet(schema_version="v0", tags={"intent": "memory"})
        block = MemoryBlock(
            content="note",
            tags=tags,
            provenance={"source": "unit_test"},
            lane="episodic",
            confidence=0.9,
        )
        payload = block.to_dict()
        json.dumps(payload)

    def test_writeback_package(self) -> None:
        tags = TagSet(schema_version="v0", tags={"intent": "writeback"})
        package = WritebackPackage(
            episode="episode",
            distilled_facts=["fact"],
            procedural_snippet=None,
            tags=tags,
            evaluation_outcome="ok",
            promotion_notes="promoted",
            demotion_notes=None,
        )
        payload = package.to_dict()
        json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
