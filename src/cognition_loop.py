"""Minimal cognition loop."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from .contracts import EventRecord
from .cognition.config import EngineConfig
from .cognition.engine import CognitionEngine
from .runs.session import create_run_dir


def run_cognition_loop(
    task: str,
    storage_dir: Path,
    *,
    cognition_backend: str = "fallback",
    model_endpoint: Optional[str] = None,
) -> EventRecord:
    """Entrypoint that routes the original loop interface to the new Engine."""
    config = EngineConfig(
        cognition_backend=cognition_backend,
        model_endpoint=model_endpoint
    )
    engine = CognitionEngine(config)
    
    # Engine requires a unique run_dir inside storage_dir/.runs per CX-008
    storage_dir = Path(storage_dir)
    run_dir = create_run_dir(storage_dir)
    
    return engine.run(task, run_dir)
