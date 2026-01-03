import tempfile
import unittest
from pathlib import Path

from src.contracts import EventRecord, QueryPlan, TagSet
from src.eventlog import EventLog


class EventLogTest(unittest.TestCase):
    def test_write_and_read(self) -> None:
        tags = TagSet(schema_version="v0", tags={"intent": "eventlog"})
        query_plan = QueryPlan(filters={}, limits=0, recency_bias=0.0)
        record = EventRecord(
            task="log",
            tags=tags,
            query_plan=query_plan,
            retrieved_ids=[],
            actions=["event_log"],
            tool_calls=[],
            validations=["contracts_v0"],
            outcome="success",
            provenance={"source": "unit_test"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "eventlog.jsonl"
            log = EventLog(log_path)
            log.append(record)
            records = log.read_all()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].task, "log")


if __name__ == "__main__":
    unittest.main()
