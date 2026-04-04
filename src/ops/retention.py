"""Run artifact retention planning."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from typing import Dict, List


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass
class RunRetentionPolicy:
    max_age_days: int = 30
    max_total_bytes: int = 2_147_483_648
    keep_minimum: int = 20

    @classmethod
    def from_env(cls) -> "RunRetentionPolicy":
        return cls(
            max_age_days=_env_int("LIBR8_RETENTION_MAX_AGE_DAYS", 30),
            max_total_bytes=_env_int("LIBR8_RETENTION_MAX_TOTAL_BYTES", 2_147_483_648),
            keep_minimum=_env_int("LIBR8_RETENTION_KEEP_MINIMUM", 20),
        )


@dataclass
class RetentionDecision:
    run_dir: Path
    reason: str
    pinned: bool
    size_bytes: int


def _load_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _run_size_bytes(run_dir: Path) -> int:
    total = 0
    for path in run_dir.rglob("*"):
        if path.is_file():
            total += path.stat().st_size
    return total


def _is_pinned(run_dir: Path) -> bool:
    if (run_dir / ".pinned").exists() or (run_dir / "pin.json").exists():
        return True
    promotion = _load_json(run_dir / "promotion.json")
    if promotion.get("promoted"):
        return True
    manifest = _load_json(run_dir / "run_manifest.json")
    return bool(manifest.get("pinned"))


def plan_run_prune(base_dir: Path | str, policy: RunRetentionPolicy, now: datetime | None = None) -> List[RetentionDecision]:
    base_path = Path(base_dir)
    runs_dir = base_path / ".runs"
    if not runs_dir.exists():
        return []

    now = now or datetime.now(timezone.utc)
    run_dirs = [path for path in runs_dir.iterdir() if path.is_dir()]
    run_dirs.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    protected = set(run_dirs[: max(policy.keep_minimum, 0)])

    decisions: List[RetentionDecision] = []
    total_bytes = sum(_run_size_bytes(run_dir) for run_dir in run_dirs)
    age_cutoff = now - timedelta(days=max(policy.max_age_days, 0))

    for run_dir in reversed(run_dirs):
        pinned = _is_pinned(run_dir)
        size_bytes = _run_size_bytes(run_dir)
        mtime = datetime.fromtimestamp(run_dir.stat().st_mtime, tz=timezone.utc)
        over_age = mtime < age_cutoff
        over_budget = total_bytes > policy.max_total_bytes
        if pinned or run_dir in protected:
            continue
        if over_age:
            decisions.append(RetentionDecision(run_dir, "age", pinned, size_bytes))
            total_bytes -= size_bytes
            continue
        if over_budget:
            decisions.append(RetentionDecision(run_dir, "size", pinned, size_bytes))
            total_bytes -= size_bytes

    return decisions
