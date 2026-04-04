import json
import unittest

from src.contracts import (
    EventRecord,
    MemoryBlock,
    QueryPlan,
    SCHEMA_VERSION,
    TagSet,
    WritebackPackage,
)


class ContractsTest(unittest.TestCase):
    def test_event_record_json_roundtrip(self) -> None:
        tags = TagSet(schema_version=SCHEMA_VERSION, tags={"intent": "test"}, uncertainty={"intent": 0.1})
        query_plan = QueryPlan(filters={"intent": "test"}, limits=1, recency_bias=0.5)
        event = EventRecord(
            task="demo",
            tags=tags,
            query_plan=query_plan,
            retrieved_ids=[],
            actions=["tag_extraction"],
            tool_calls=[{"name": "tagger"}],
            validations=["contracts_v1_strict"],
            outcome="success",
            provenance={"source": "unit_test"},
            version_info={"core_engine": "0.1.0", "plugin_set": "none"},
        )
        payload = event.to_dict()
        json.dumps(payload)
        rehydrated = EventRecord.from_dict(payload)
        self.assertEqual(rehydrated.task, "demo")
        self.assertEqual(rehydrated.schema_version, SCHEMA_VERSION)
        self.assertEqual(rehydrated.version_info["core_engine"], "0.1.0")

    def test_memory_block_validation(self) -> None:
        tags = TagSet(schema_version=SCHEMA_VERSION, tags={"intent": "memory"})
        block = MemoryBlock(
            content="note",
            tags=tags,
            provenance={"source": "unit_test"},
            lane="episodic",
            confidence=0.9,
            version_info={"core_engine": "0.1.0", "active_procedure": "none"},
        )
        payload = block.to_dict()
        json.dumps(payload)
        self.assertEqual(payload["schema_version"], SCHEMA_VERSION)
        self.assertEqual(payload["version_info"]["active_procedure"], "none")

    def test_writeback_package(self) -> None:
        tags = TagSet(schema_version=SCHEMA_VERSION, tags={"intent": "writeback"})
        package = WritebackPackage(
            episode="episode",
            distilled_facts=["fact"],
            procedural_snippet=None,
            tags=tags,
            evaluation_outcome="ok",
            version_info={"core_engine": "0.1.0", "plugin_set": "builtin_v1"},
            promotion_notes="promoted",
            demotion_notes=None,
        )
        payload = package.to_dict()
        json.dumps(payload)
        self.assertEqual(payload["schema_version"], SCHEMA_VERSION)
        self.assertEqual(payload["version_info"]["plugin_set"], "builtin_v1")


if __name__ == "__main__":
    unittest.main()
