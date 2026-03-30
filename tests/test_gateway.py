"""Gateway testing with strict tool boundaries."""
import unittest
import os
from src.tools.contracts import ToolRequest, ApprovalContext
from src.tools.policy import ToolPolicy
from src.tools.registry import ToolRegistry
from src.tools.gateway import ExecutionGateway
from src.tools.standard import register_standard_tools

class TestExecutionGateway(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        register_standard_tools(self.registry)
        
    def test_missing_approval_denies_write(self):
        policy = ToolPolicy("write", True, [])
        gateway = ExecutionGateway(self.registry, policy)
        req = ToolRequest("write_file", {"path": "/tmp/test.txt", "content": "123"})
        res, dp = gateway.execute(req, approval=None)
        
        self.assertEqual(res.status, "denied")
        self.assertEqual(res.error_class, "policy_violation_missing_approval")
        
    def test_read_only_mode_denies_write_even_with_approval(self):
        policy = ToolPolicy("read_only", True, [])
        gateway = ExecutionGateway(self.registry, policy)
        
        ctx = ApprovalContext("test", "test")
        req = ToolRequest("write_file", {"path": "/tmp/test.txt", "content": "123"})
        res, dp = gateway.execute(req, approval=ctx)
        
        self.assertEqual(res.status, "denied")
        self.assertEqual(res.error_class, "policy_violation_write_in_read_only")
        
    def test_path_normalization_enforces_bounds(self):
        base_dir = os.path.realpath(os.path.abspath("."))
        policy = ToolPolicy("read_only", True, [base_dir])
        gateway = ExecutionGateway(self.registry, policy)
        
        req = ToolRequest("list_directory", {"path": "../../../../../../etc"})
        res, dp = gateway.execute(req, approval=None)
        
        self.assertEqual(res.status, "denied")
        self.assertEqual(res.error_class, "policy_violation_path_escape")

if __name__ == "__main__":
    unittest.main()
