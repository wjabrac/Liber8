import tempfile
import unittest
import os
from pathlib import Path

from src.service.app import Libr8Service
from src.service.config import ServiceConfig

class TestLivePostgres(unittest.TestCase):
    def setUp(self):
        self.dsn = os.environ.get("TEST_POSTGRES_DSN", "postgres://postgres:mysecretpassword@127.0.0.1:5432/libr8_test")
        
    @unittest.skipUnless(os.environ.get("LIVE_POSTGRES"), "Requires active PostgreSQL to test live store")
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

    @unittest.skipUnless(os.environ.get("LIVE_POSTGRES"), "Requires active PostgreSQL to test live store")
    def test_postgres_auto_migration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # This should trigger MigrationRunner.apply_migrations() in Libr8Service.__init__
            service = Libr8Service(ServiceConfig(
                storage_dir=tmpdir,
                state_store_backend="postgres",
                postgres_dsn=self.dsn,
                auto_migrate=True
            ))
            
            # If auto_migrate worked, we should be able to submit a task immediately
            # (the table service_runs should have been created by 001_service_schema.sql)
            result = service.submit_task("auto migration test task")
            self.assertEqual(result["status"], "completed")
            
            # Verify record via direct state access
            record = service.state.get_record(result["task_id"])
            self.assertIsNotNone(record)

if __name__ == "__main__":
    unittest.main()
