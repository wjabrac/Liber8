"""Tagger wrapper with fake backend support."""

from __future__ import annotations

import os
from typing import Any, Dict

from .contracts import TagSet


class Tagger:
    def __init__(self, fake_backend: bool = False) -> None:
        self.fake_backend = fake_backend
        self.model_endpoint = os.getenv("LIBR8_MODEL_ENDPOINT")
        if not self.fake_backend and not self.model_endpoint:
            raise RuntimeError("LIBR8_MODEL_ENDPOINT must be set when not using fake backend")

    def extract_tags(self, task: str) -> TagSet:
        if self.fake_backend:
            tags: Dict[str, Any] = {
                "intent": "fake",
                "task_length": len(task),
                "task_prefix": task[:12],
            }
            return TagSet(schema_version="v0", tags=tags, uncertainty={"intent": 0.0})
        # NOTE: Backend integration is a stub unless an HTTP call is implemented.
        tags = {
            "intent": "backend_stub",
            "backend": "stub",
            "endpoint": self.model_endpoint,
            "task_length": len(task),
        }
        return TagSet(schema_version="v0", tags=tags, uncertainty={"intent": 0.2})
