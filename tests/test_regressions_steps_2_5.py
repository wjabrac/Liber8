import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from main import main as app_main
from src.cli import main as cli_main
from src.cognition.config import EngineConfig
from src.cognition.engine import CognitionEngine
from src.contracts import QueryPlan, SCHEMA_VERSION, TagSet
from src.eventlog import EventLog
from src.runs.state import RunState
from src.tools.contracts import ToolRequest
from src.tools.gateway import ExecutionGateway
from src.tools.policy import ToolPolicy
from src.tools.registry import ToolRegistry
from src.tools.standard import register_standard_tools


class TestRegressionsSteps2To5(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.tempdir.name) / "run"
        self.engine = CognitionEngine(EngineConfig(cognition_backend="dspy+zep", retry_backoff_base_sec=0.0))

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _state(self) -> RunState:
        return RunState(
            task="retry test",
            status="running",
            current_step=5,
            attempt=1,
            state_snapshot={"selected_agents": ["researcher", "synthesizer"], "active_backend": "dspy+zep"},
        )

    def test_retry_actions_are_explicitly_applied(self) -> None:
        state = self._state()
        with mock.patch("src.cognition.engine.time.sleep"):
            self.engine._apply_retry_decision("retry_fixed", self.run_dir, state, {})
        self.assertEqual(state.attempt, 2)

        state = self._state()
        self.engine._apply_retry_decision("switch_tool", self.run_dir, state, {"reason": "tool failed"})
        self.assertTrue(state.state_snapshot["disable_tools"])
        self.assertEqual(state.state_snapshot["selected_agents"], ["synthesizer"])

        state = self._state()
        self.engine._apply_retry_decision("ask_for_approval", self.run_dir, state, {"reason": "approval"})
        self.assertIn("approval_required", state.state_snapshot)
        self.assertTrue(state.state_snapshot["disable_tools"])

        state = self._state()
        self.engine._apply_retry_decision("switch_tier", self.run_dir, state, {})
        self.assertEqual(self.engine.active_backend, "fallback")
        self.assertEqual(state.state_snapshot["memory_backend"], "fallback")

        state = self._state()
        self.engine._apply_retry_decision("enter_degraded_mode", self.run_dir, state, {})
        self.assertEqual(state.state_snapshot["memory_backend"], "fallback")

        state = self._state()
        with mock.patch("src.cognition.engine.time.sleep"):
            self.engine._apply_retry_decision("exponential_backoff", self.run_dir, state, {})
        self.assertEqual(state.attempt, 2)

    def test_gateway_blocks_sibling_prefix_escape(self) -> None:
        registry = ToolRegistry()
        register_standard_tools(registry)
        allowed_root = self.run_dir / "allowed"
        policy = ToolPolicy("read_only", False, [str(allowed_root)])
        gateway = ExecutionGateway(registry, policy)

        sibling = str(self.run_dir / "allowed-evil")
        result, _ = gateway.execute(ToolRequest("list_directory", {"path": sibling}))
        self.assertEqual(result.status, "denied")
        self.assertEqual(result.error_class, "policy_violation_path_escape")

    def test_cli_and_main_accept_one_shared_interface(self) -> None:
        storage_dir = Path(self.tempdir.name) / "storage"
        argv = ["run", "shared interface", "--storage-dir", str(storage_dir), "--backend", "fallback"]
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            cli_rc = cli_main(argv)
            app_rc = app_main(argv)
        output = stdout.getvalue()
        self.assertEqual(cli_rc, 0)
        self.assertEqual(app_rc, 0)
        run_dirs = list((storage_dir / ".runs").glob("*"))
        self.assertEqual(len(run_dirs), 2)
        for run_dir in run_dirs:
            self.assertIn(str(run_dir), output)

    def test_eventlog_upcasts_only_on_read_boundary(self) -> None:
        raw_event = {
            "task": "legacy",
            "outcome": "completed",
            "tags": {"tags": {}},
            "query_plan": {"filters": {}, "limits": 0, "recency_bias": 0.0},
            "retrieved_ids": [],
            "actions": [],
            "validations": [],
            "provenance": {},
        }
        eventlog = self.run_dir / "eventlog.jsonl"
        eventlog.parent.mkdir(parents=True, exist_ok=True)
        eventlog.write_text(json.dumps(raw_event) + "\n", encoding="utf-8")

        record = EventLog(eventlog).read_all()[0]
        self.assertEqual(record.schema_version, SCHEMA_VERSION)
        self.assertEqual(record.tags.schema_version, SCHEMA_VERSION)
        self.assertEqual(record.outcome, "success")


if __name__ == "__main__":
    unittest.main()
