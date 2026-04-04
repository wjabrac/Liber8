import unittest

from src.service.workflows.approvals import ApprovalRequest, InMemoryApprovalQueue


class TestApprovalQueue(unittest.TestCase):
    def test_submit_and_resolve_approval(self) -> None:
        queue = InMemoryApprovalQueue()
        request = ApprovalRequest(request_id="req-1", task_id="task-1", scope="tool.write", reason="mutation path")

        queue.submit(request)
        resolved = queue.resolve("req-1", "approved")

        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.status, "approved")
        self.assertEqual(queue.pending(), [])


if __name__ == "__main__":
    unittest.main()
