"""Configuration models for the Cognition Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class EngineConfig:
    cognition_backend: str = "fallback"  # Can be 'dspy+zep' or 'fallback'
    engine_version: str = "0.1.0"
    model_endpoint: Optional[str] = None
    
    # Tool policy
    tool_policy_mode: str = "read_only"  # 'read_only' or 'write'
    path_allowlists: List[str] = field(default_factory=lambda: ["/home/willux/LIBR8_WORKSPACE", ".runs"])
    network_allowed: bool = False
    
    # Retry behavior
    retry_max_attempts: int = 3
    retry_backoff_base_sec: float = 1.0
    
    # Feature toggles
    rust_acceleration_toggles: Dict[str, bool] = field(default_factory=lambda: {
        "retrieval_ranking": False,
        "replay_aggregation": False
    })
    
    # Trace & artifacts
    trace_verbosity: str = "default"
    run_artifact_limits: int = 100
    
    @property
    def config_hash(self) -> str:
        # A simple naive hash for provenance tracking.
        return f"{self.cognition_backend}-{self.engine_version}-{self.tool_policy_mode}"
