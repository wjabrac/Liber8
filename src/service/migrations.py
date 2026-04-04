"""Database migration helpers for the LIBR8 operational plane."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
from typing import Dict, List


def migrations_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "sql" / "postgres"


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
