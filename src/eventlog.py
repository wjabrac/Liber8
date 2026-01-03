"""Filesystem event log for EventRecords."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from .contracts import EventRecord


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: EventRecord) -> None:
        payload = record.to_dict()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload))
            handle.write("\n")

    def read_all(self) -> List[EventRecord]:
        if not self.path.exists():
            return []
        records: List[EventRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(EventRecord.from_dict(json.loads(line)))
        return records


def write_event_record(path: Path, record: EventRecord) -> None:
    EventLog(path).append(record)


def write_event_records(path: Path, records: Iterable[EventRecord]) -> None:
    log = EventLog(path)
    for record in records:
        log.append(record)
