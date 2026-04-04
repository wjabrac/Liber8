"""Router compatibility wrapper over the canonical cognition engine."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from src.cognition.config import EngineConfig
from src.cognition.engine import CognitionEngine
from src.contracts import EventRecord


def run_router(
    task: str,
    storage_dir: Path,
    *,
    fake_backend: bool = False,
    model_endpoint: Optional[str] = None,
) -> EventRecord:
    storage_dir = Path(storage_dir)
    backend = "fallback" if fake_backend else os.getenv("LIBR8_ROUTER_BACKEND", "fallback")
    engine = CognitionEngine(
        EngineConfig(
            cognition_backend=backend,
            model_endpoint=model_endpoint,
        )
    )
    return engine.run(task, storage_dir)
