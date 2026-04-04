import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.ops.retention import RunRetentionPolicy, plan_run_prune


class TestRetentionPolicy(unittest.TestCase):
    def test_age_and_pin_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            runs = base / ".runs"
            runs.mkdir()

            old_run = runs / "old-run"
            old_run.mkdir()
            (old_run / "trace.jsonl").write_text("{}\n", encoding="utf-8")

            pinned_run = runs / "pinned-run"
            pinned_run.mkdir()
            (pinned_run / ".pinned").write_text("keep", encoding="utf-8")
            (pinned_run / "trace.jsonl").write_text("{}\n", encoding="utf-8")

            promoted_run = runs / "promoted-run"
            promoted_run.mkdir()
            (promoted_run / "promotion.json").write_text(json.dumps({"promoted": True}), encoding="utf-8")
            (promoted_run / "trace.jsonl").write_text("{}\n", encoding="utf-8")

            old_ts = (datetime.now(timezone.utc) - timedelta(days=45)).timestamp()
            os.utime(old_run, (old_ts, old_ts))
            os.utime(pinned_run, (old_ts, old_ts))
            os.utime(promoted_run, (old_ts, old_ts))

            removable = plan_run_prune(base, RunRetentionPolicy(max_age_days=30, max_total_bytes=10_000_000, keep_minimum=0))
            paths = {item.run_dir.name for item in removable}

            self.assertIn("old-run", paths)
            self.assertNotIn("pinned-run", paths)
            self.assertNotIn("promoted-run", paths)


if __name__ == "__main__":
    unittest.main()
