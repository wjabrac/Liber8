"""Tests for schema versions and artifact migrations."""
import unittest
from src.contracts.migration import upcast_event, upcast_trace

class TestMigrationDiscipline(unittest.TestCase):
    def test_upcast_v0_event(self):
        v0_event = {
            "task": "summarize this",
            "outcome": "completed",
            "tags": {"tags": {}},
            "query_plan": {"filters": {}, "limits": 5, "recency_bias": 1.0},
            "retrieved_ids": [],
            "actions": [],
            "validations": [],
            "provenance": {}
        }
        
        v1_event = upcast_event(v0_event)
        
        self.assertEqual(v1_event["schema_version"], "1.0")
        self.assertEqual(v1_event["outcome"], "success")
        self.assertIn("tool_calls", v1_event)
        self.assertEqual(v1_event["tags"]["schema_version"], "1.0")
        self.assertEqual(v1_event["query_plan"]["schema_version"], "1.0")
        
    def test_upcast_v0_trace(self):
        v0_trace = {
            "task": "trace job",
            "outcome": "completed",
            "tags": {"tags": {}}
        }
        
        v1_trace = upcast_trace(v0_trace)
        
        self.assertEqual(v1_trace["schema_version"], "1.0")
        self.assertEqual(v1_trace["outcome"], "success")
        self.assertEqual(v1_trace["tags"]["schema_version"], "1.0")

if __name__ == "__main__":
    unittest.main()
