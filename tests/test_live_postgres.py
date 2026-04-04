import tempfile
import unittest
import os
from pathlib import Path

from src.service.app import Libr8Service
from src.service.config import ServiceConfig

class TestLivePostgres(unittest.TestCase):
    def setUp(self):
        self.dsn = os.environ.get("TEST_POSTGRES_DSN", "postgres://postgres:mysecretpassword@127.0.0.1:5432/libr8_test")
        
    def test_postgres_store_records_and_updates_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(
                storage_dir=tmpdir, 
                cognition_backend="fallback",
                state_store_backend="postgres",
                postgres_dsn=self.dsn
            ))
            
            # submit task
            result = service.submit_task("live postgres test task")
            self.assertEqual(result["status"], "completed")
            
            # verify record saved in DB
            record = service.state.get_record(result["task_id"])
            self.assertIsNotNone(record)
            self.assertEqual(record.task, "live postgres test task")
            self.assertEqual(record.outcome, result["outcome"])

if __name__ == "__main__":
    unittest.main()
