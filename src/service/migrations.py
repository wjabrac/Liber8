"""Database migration helpers for the LIBR8 operational plane."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
from typing import Dict, List

try:
    import psycopg
except ImportError:
    psycopg = None

def migrations_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "sql" / "postgres"


class MigrationHashMismatchError(RuntimeError):
    """Raised when an already-applied migration has a different digest on disk."""


@dataclass
class MigrationFile:
    name: str
    path: str
    sha256: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def list_postgres_migrations() -> List[MigrationFile]:
    root = migrations_dir()
    if not root.exists():
        return []
    records: List[MigrationFile] = []
    for path in sorted(root.glob("*.sql")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append(MigrationFile(name=path.name, path=str(path), sha256=digest))
    return records


class MigrationRunner:
    def __init__(self, dsn: str, *, migrations_root: Path | None = None):
        self.dsn = dsn
        self._migrations_root = migrations_root
        if psycopg is None:
            raise RuntimeError("psycopg is not installed; migrations unavailable.")

    def _available_migrations(self) -> List[MigrationFile]:
        if self._migrations_root is None:
            return list_postgres_migrations()
        records: List[MigrationFile] = []
        for path in sorted(self._migrations_root.glob("*.sql")):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            records.append(MigrationFile(name=path.name, path=str(path), sha256=digest))
        return records

    def ensure_log_table(self):
        with psycopg.connect(self.dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS migrations_log (
                        name TEXT PRIMARY KEY,
                        applied_at TIMESTAMPTZ DEFAULT NOW(),
                        sha256 TEXT NOT NULL
                    )
                    """
                )

    def get_applied_migrations(self) -> Dict[str, str]:
        self.ensure_log_table()
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name, sha256 FROM migrations_log")
                return {row[0]: row[1] for row in cur.fetchall()}

    def apply_migrations(self) -> List[str]:
        applied = self.get_applied_migrations()
        available = self._available_migrations()
        newly_applied = []

        for migration in available:
            if migration.name in applied:
                if applied[migration.name] != migration.sha256:
                    raise MigrationHashMismatchError(
                        f"Migration {migration.name} hash mismatch: database={applied[migration.name]} filesystem={migration.sha256}"
                    )
                continue

            print(f"Applying {migration.name}...")
            sql = Path(migration.path).read_text()
            with psycopg.connect(self.dsn, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    cur.execute(
                        "INSERT INTO migrations_log (name, sha256) VALUES (%s, %s)",
                        (migration.name, migration.sha256)
                    )
            newly_applied.append(migration.name)
            print(f"Applied {migration.name}")
        
        return newly_applied
