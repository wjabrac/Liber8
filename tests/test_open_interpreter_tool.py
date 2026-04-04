import tempfile
import unittest
from pathlib import Path

from src.tools.contracts import ApprovalContext, ToolRequest
from src.tools.gateway import ExecutionGateway
from src.tools.policy import ToolPolicy
from src.tools.registry import ToolRegistry
from src.tools.standard import register_standard_tools


class TestOpenInterpreterTool(unittest.TestCase):
    def test_open_interpreter_executes_inside_declared_sandbox(self) -> None:
        registry = ToolRegistry()
        register_standard_tools(registry)
        gateway = ExecutionGateway(registry, ToolPolicy("write", False, []))
        with tempfile.TemporaryDirectory() as tmpdir:
            req = ToolRequest(
                "open_interpreter",
                {
                    "command": "echo approved",
                    "approval_token": "APPROVE: echo approved",
                    "timeout": 2.0,
                    "sandbox_root": tmpdir,
                    "working_directory": tmpdir,
                },
            )
            result, _ = gateway.execute(req, approval=ApprovalContext("test", "tool approved"))

        self.assertEqual(result.status, "success")
        self.assertEqual(result.output["status"], "executed")
        self.assertTrue(result.output["allowed"])
        self.assertEqual(result.output["sandbox_root"], str(Path(tmpdir).resolve()))

    def test_open_interpreter_blocks_paths_outside_sandbox(self) -> None:
        registry = ToolRegistry()
        register_standard_tools(registry)
        gateway = ExecutionGateway(registry, ToolPolicy("write", False, []))
        with tempfile.TemporaryDirectory() as tmpdir:
            outside = Path(tmpdir).parent / "outside.txt"
            req = ToolRequest(
                "open_interpreter",
                {
                    "command": f"type {outside}",
                    "approval_token": f"APPROVE: type {outside}",
                    "timeout": 2.0,
                    "sandbox_root": tmpdir,
                    "working_directory": tmpdir,
                },
            )
            result, _ = gateway.execute(req, approval=ApprovalContext("test", "tool approved"))

        self.assertEqual(result.status, "success")
        self.assertEqual(result.output["status"], "blocked")
        self.assertFalse(result.output["allowed"])
        self.assertIn("outside sandbox", result.output["stderr"])


if __name__ == "__main__":
    unittest.main()
