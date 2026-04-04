"""Artifact indexing helpers for service-side operations."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class ArtifactRecord:
    run_id: str
    artifact_kind: str
    artifact_path: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def _load_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def index_run_artifacts(run_dir: Path | str) -> List[ArtifactRecord]:
    path = Path(run_dir)
    manifest = _load_json(path / "run_manifest.json")
    artifacts = (manifest.get("artifacts") or {}) if manifest else {}
    records: List[ArtifactRecord] = []
    for kind, artifact_path in sorted(artifacts.items()):
        records.append(ArtifactRecord(run_id=path.name, artifact_kind=str(kind), artifact_path=str(artifact_path)))
    if not records:
        for fallback in ["meta.json", "eventlog.jsonl", "trace.jsonl", "memory.jsonl", "writeback.json", "promotion.json", "run_manifest.json"]:
            candidate = path / fallback
            if candidate.exists():
                records.append(ArtifactRecord(run_id=path.name, artifact_kind=candidate.stem, artifact_path=str(candidate)))
    return records
