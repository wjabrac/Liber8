import tempfile
import unittest
from pathlib import Path
from src.service.app import Libr8Service
from src.service.config import ServiceConfig

class TestServiceDurability(unittest.TestCase):
    """Tests for file-backed workflow persistence (approvals, exports)."""
    
    def test_workflow_persistence_across_restarts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ServiceConfig(storage_dir=tmpdir)
            
            # 1. Start first instance
            service1 = Libr8Service(config)
            
            # 2. Submit a task to get a run_id (using default memory backend for run records)
            run_result = service1.submit_task("durability test task")
            run_id = run_result["run_id"]
            task_id = run_result["task_id"]
            
            # 3. Submit an export job and an approval request
            export_job = service1.submit_export_job(run_id)
            approval_req = service1.submit_approval(task_id, "tool.write", "test durability")
            
            export_id = export_job["job_id"]
            approval_id = approval_req["request_id"]
            
            # 4. Verify they exist in service1
            self.assertEqual(len(service1.list_export_jobs()["jobs"]), 1)
            self.assertEqual(len(service1.list_pending_approvals()["pending"]), 1)
            
            # 5. "Restart" - create new service instance with same storage_dir
            service2 = Libr8Service(config)
            
            # 6. Verify they still exist in service2 (persisted via files in .service_state/)
            exports2 = service2.list_export_jobs()["jobs"]
            approvals2 = service2.list_pending_approvals()["pending"]
            
            self.assertEqual(len(exports2), 1)
            self.assertEqual(exports2[0]["job_id"], export_id)
            self.assertEqual(exports2[0]["run_id"], run_id)
            
            self.assertEqual(len(approvals2), 1)
            self.assertEqual(approvals2[0]["request_id"], approval_id)
            self.assertEqual(approvals2[0]["task_id"], task_id)

if __name__ == "__main__":
    unittest.main()
