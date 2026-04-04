"""Configuration models for the Cognition Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Dict, List, Optional


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_path_allowlists() -> List[str]:
    raw_value = os.getenv("LIBR8_PATH_ALLOWLIST")
    if raw_value:
        return [entry for entry in raw_value.split(os.pathsep) if entry]
    return [str(_project_root())]


def _default_role_model_policy() -> Dict[str, str]:
    raw_value = os.getenv("LIBR8_ROLE_MODEL_POLICY")
    if raw_value:
        try:
            parsed = json.loads(raw_value)
            if isinstance(parsed, dict):
                return {str(key): str(value) for key, value in parsed.items()}
        except json.JSONDecodeError:
            pass
    return {
        "planning": "dspy_planner",
        "execution": "local_executor",
        "programming": "fallback_coder",
        "critique": "fallback_critic",
        "style": "fallback_style",
        "research": "fallback_research",
    }


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class EngineConfig:
    cognition_backend: str = "fallback"
    engine_version: str = "0.1.0"
    model_endpoint: Optional[str] = None

    tool_policy_mode: str = "write"
    path_allowlists: List[str] = field(default_factory=_default_path_allowlists)
    network_allowed: bool = False
    enforce_isolation_for_writes: bool = field(default_factory=lambda: _env_flag("LIBR8_REQUIRE_ISOLATION_FOR_WRITES", False))
    execution_isolation_backend: str = field(default_factory=lambda: os.getenv("LIBR8_EXECUTION_ISOLATION_BACKEND", "none"))

    retry_max_attempts: int = 3
    retry_backoff_base_sec: float = 1.0

    rust_acceleration_toggles: Dict[str, bool] = field(default_factory=lambda: {
        "retrieval_ranking": False,
        "replay_aggregation": False,
    })
    role_model_policy: Dict[str, str] = field(default_factory=_default_role_model_policy)

    trace_verbosity: str = "default"
    run_artifact_limits: int = 100

    @property
    def config_hash(self) -> str:
        return f"{self.cognition_backend}-{self.engine_version}-{self.tool_policy_mode}-{self.execution_isolation_backend}"
