"""Optional PostgreSQL-backed service state store."""

from __future__ import annotations

from typing import Dict

from src.service.models import RunRecord

try:
    import psycopg
except Exception:  # pragma: no cover - optional dependency path
    psycopg = None


class PostgresServiceStateStore:
    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise RuntimeError("PostgreSQL DSN is required for the postgres state store.")
        if psycopg is None:
            raise RuntimeError("psycopg is not installed; PostgreSQL state store is unavailable.")
        self.dsn = dsn

    def record_submission(self, record: RunRecord) -> None:
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO service_runs (task_id, run_id, task, status, outcome, artifact_dir, failure_class, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (task_id) DO UPDATE SET
                        run_id = EXCLUDED.run_id,
                        task = EXCLUDED.task,
                        status = EXCLUDED.status,
                        outcome = EXCLUDED.outcome,
                        artifact_dir = EXCLUDED.artifact_dir,
                        failure_class = EXCLUDED.failure_class,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        record.task_id,
                        record.run_id,
                        record.task,
                        record.status,
                        record.outcome,
                        record.artifact_dir,
                        record.failure_class,
                        record.created_at,
                        record.updated_at,
                    ),
                )

    def update_record(self, task_id: str, **updates: str | None) -> RunRecord | None:
        columns = {key: value for key, value in updates.items() if key in {"status", "outcome", "artifact_dir", "failure_class"}}
        if not columns:
            return self.get_record(task_id)

        assignments = ", ".join(f"{key} = %s" for key in columns)
        values = list(columns.values()) + [task_id]
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE service_runs SET {assignments}, updated_at = NOW() WHERE task_id = %s", values)
        return self.get_record(task_id)

    def get_record(self, task_id: str) -> RunRecord | None:
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT task_id, run_id, task, status, outcome, created_at, updated_at, artifact_dir, failure_class FROM service_runs WHERE task_id = %s",
                    (task_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return RunRecord(
            task_id=row[0],
            run_id=row[1],
            task=row[2],
            status=row[3],
            outcome=row[4],
            created_at=row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5]),
            updated_at=row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
            artifact_dir=row[7],
            failure_class=row[8],
        )

    def summary(self) -> Dict[str, object]:
        try:
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT to_regclass('public.service_runs')")
                    has_table = cur.fetchone()[0] is not None
                    if has_table:
                        cur.execute("SELECT status, COUNT(*) FROM service_runs GROUP BY status")
                        rows = cur.fetchall()
                    else:
                        rows = []
            return {
                "backend": "postgres",
                "configured": True,
                "implemented": True,
                "database_available": True,
                "schema_ready": has_table,
                "statuses": {status: count for status, count in rows},
            }
        except Exception as e:
            return {
                "backend": "postgres",
                "configured": True,
                "implemented": True,
                "database_available": False,
                "schema_ready": False,
                "error": str(e),
                "statuses": {},
            }
