"""Runtime configuration for the LIBR8 service layer."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any, Dict

from src.cognition.config import EngineConfig
from src.ops.retention import RunRetentionPolicy


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass
class ServiceConfig:
    host: str = field(default_factory=lambda: os.getenv("LIBR8_SERVICE_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: _env_int("LIBR8_SERVICE_PORT", 8080))
    storage_dir: str = field(default_factory=lambda: os.getenv("LIBR8_STORAGE_DIR", ".storage"))
    cognition_backend: str = field(default_factory=lambda: os.getenv("LIBR8_COGNITION_BACKEND", "fallback"))
    state_store_backend: str = field(default_factory=lambda: os.getenv("LIBR8_STATE_STORE_BACKEND", "memory"))
    postgres_dsn: str | None = field(default_factory=lambda: os.getenv("LIBR8_POSTGRES_DSN"))
    log_level: str = field(default_factory=lambda: os.getenv("LIBR8_LOG_LEVEL", "INFO"))
    log_json: bool = field(default_factory=lambda: _env_flag("LIBR8_LOG_JSON", True))
    require_isolation_for_writes: bool = field(default_factory=lambda: _env_flag("LIBR8_REQUIRE_ISOLATION_FOR_WRITES", False))
    execution_isolation_backend: str = field(default_factory=lambda: os.getenv("LIBR8_EXECUTION_ISOLATION_BACKEND", "none"))
    retention_policy: RunRetentionPolicy = field(default_factory=RunRetentionPolicy.from_env)

    def to_engine_config(self) -> EngineConfig:
        return EngineConfig(
            cognition_backend=self.cognition_backend,
            enforce_isolation_for_writes=self.require_isolation_for_writes,
            execution_isolation_backend=self.execution_isolation_backend,
        )

    @property
    def storage_path(self) -> Path:
        return Path(self.storage_dir)

    def public_snapshot(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "storage_dir": self.storage_dir,
            "cognition_backend": self.cognition_backend,
            "state_store_backend": self.state_store_backend,
            "postgres_dsn_configured": bool(self.postgres_dsn),
            "log_level": self.log_level,
            "log_json": self.log_json,
            "require_isolation_for_writes": self.require_isolation_for_writes,
            "execution_isolation_backend": self.execution_isolation_backend,
            "retention_policy": {
                "max_age_days": self.retention_policy.max_age_days,
                "max_total_bytes": self.retention_policy.max_total_bytes,
                "keep_minimum": self.retention_policy.keep_minimum,
            },
        }
