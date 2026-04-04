import tempfile
import unittest
from pathlib import Path

from src.contracts import EventRecord, QueryPlan, SCHEMA_VERSION, TagSet
from src.eventlog import EventLog


class EventLogTest(unittest.TestCase):
    def test_write_and_read(self) -> None:
        tags = TagSet(schema_version=SCHEMA_VERSION, tags={"intent": "eventlog"})
        query_plan = QueryPlan(filters={}, limits=0, recency_bias=0.0)
        record = EventRecord(
            task="log",
            tags=tags,
            query_plan=query_plan,
            retrieved_ids=[],
            actions=["event_log"],
            tool_calls=[],
            validations=["contracts_v1_strict"],
            outcome="success",
            provenance={"source": "unit_test"},
            version_info={"core_engine": "0.1.0", "plugin_set": "none"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "eventlog.jsonl"
            log = EventLog(log_path)
            log.append(record)
            records = log.read_all()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].task, "log")
        self.assertEqual(records[0].schema_version, SCHEMA_VERSION)
        self.assertEqual(records[0].version_info["core_engine"], "0.1.0")


if __name__ == "__main__":
    unittest.main()
