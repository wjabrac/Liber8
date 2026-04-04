"""Structured logging helpers for service and operations."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, TextIO


class JsonLogger:
    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream = stream or sys.stdout

    def emit(self, event: str, **fields: Any) -> Dict[str, Any]:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **fields,
        }
        self.stream.write(json.dumps(payload, sort_keys=True) + "\n")
        self.stream.flush()
        return payload
