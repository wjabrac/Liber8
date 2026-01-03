"""Tagger agent wrapper."""

from __future__ import annotations

from typing import Optional

from ..contracts import TagSet
from ..tagger import Tagger


def extract_tags(task: str, *, fake_backend: bool = False, model_endpoint: Optional[str] = None) -> TagSet:
    tagger = Tagger(fake_backend=fake_backend)
    if model_endpoint is not None:
        tagger.model_endpoint = model_endpoint
    return tagger.extract_tags(task)
