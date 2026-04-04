import json
import tempfile
import unittest
from pathlib import Path

from src.cognition.config import EngineConfig
from src.cognition.engine import CognitionEngine
from src.eventlog import EventLog
from src.memory_adapter import FileSystemMemoryAdapter


class TestArchitectureGapFill(unittest.TestCase):
    def test_programming_task_records_plugins_enrichment_and_interpreter_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "plugin-run"
            engine = CognitionEngine(EngineConfig(cognition_backend="fallback"))
            event = engine.run("debug python code and patch tests", run_dir)

            trace = json.loads((run_dir / "trace.jsonl").read_text(encoding="utf-8").splitlines()[-1])

            self.assertIn("programming", event.provenance["plugins"])
            self.assertIn("codebase_files", event.provenance["enrichment"]["sources"])
            self.assertIn("programming", event.provenance["role_models"])
            self.assertTrue(event.tool_calls)
            self.assertEqual(event.tool_calls[0]["name"], "open_interpreter")
            self.assertIn("core_engine", event.version_info)
            self.assertTrue(any(span["name"] == "ai.tool.invoke" for span in trace["execution_spans"]))

    def test_writeback_and_promotion_artifacts_and_multi_lane_memory_are_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "memory-run"
            engine = CognitionEngine(EngineConfig(cognition_backend="fallback"))
            event = engine.run("create a repeatable automation procedure", run_dir)

            writeback_path = run_dir / "writeback.json"
            promotion_path = run_dir / "promotion.json"
            self.assertTrue(writeback_path.exists())
            self.assertTrue(promotion_path.exists())

            writeback_payload = json.loads(writeback_path.read_text(encoding="utf-8"))
            self.assertIn("procedural_snippet", writeback_payload)
            self.assertTrue(writeback_payload["procedural_snippet"])
            self.assertIn("version_info", writeback_payload)

            promotion_payload = json.loads(promotion_path.read_text(encoding="utf-8"))
            self.assertEqual(promotion_payload["schema_version"], "1.0")
            self.assertTrue(promotion_payload["promoted"])
            self.assertIn("procedural_memory", promotion_payload["promotion_targets"])
            self.assertEqual(event.provenance["promotion_artifact"]["schema_version"], "1.0")
            self.assertIn("version_info", promotion_payload)

            blocks = FileSystemMemoryAdapter(run_dir / "memory.jsonl").read(event.tags)
            lanes = {block.lane for block in blocks}
            self.assertIn("episodic", lanes)
            self.assertIn("semantic", lanes)
            self.assertIn("procedural", lanes)
            self.assertTrue(all(block.version_info.get("core_engine") for block in blocks))

    def test_eventlog_roundtrip_preserves_enrichment_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "event-run"
            engine = CognitionEngine(EngineConfig(cognition_backend="fallback"))
            engine.run("research and compare options", run_dir)

            event = EventLog(run_dir / "eventlog.jsonl").read_all()[0]
            self.assertIn("enrichment", event.provenance)
            self.assertTrue(event.provenance["enrichment"]["sources"])
            self.assertIn("version_info", event.provenance)


if __name__ == "__main__":
    unittest.main()
