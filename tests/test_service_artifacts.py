import json
import tempfile
import unittest
from pathlib import Path

from src.service.artifacts import index_run_artifacts


class TestServiceArtifacts(unittest.TestCase):
    def test_index_run_artifacts_prefers_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run-1"
            run_dir.mkdir()
            (run_dir / "run_manifest.json").write_text(
                json.dumps({"artifacts": {"meta": str(run_dir / "meta.json"), "trace": str(run_dir / "trace.jsonl")}}),
                encoding="utf-8",
            )

            records = index_run_artifacts(run_dir)

            self.assertEqual(len(records), 2)
            self.assertEqual(records[0].artifact_kind, "meta")
            self.assertEqual(records[1].artifact_kind, "trace")

    def test_index_run_artifacts_falls_back_to_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run-2"
            run_dir.mkdir()
            (run_dir / "meta.json").write_text("{}", encoding="utf-8")
            (run_dir / "trace.jsonl").write_text("{}\n", encoding="utf-8")

            records = index_run_artifacts(run_dir)
            kinds = {record.artifact_kind for record in records}

            self.assertIn("meta", kinds)
            self.assertIn("trace", kinds)


if __name__ == "__main__":
    unittest.main()
