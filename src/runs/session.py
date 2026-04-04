"""Session management for runs."""

import json
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def get_git_commit() -> str:
    """Retrieve the current git commit hash, safely."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def create_run_dir(base_dir: Path | str) -> Path:
    """Creates a unique per-run directory structure."""
    run_id = str(uuid.uuid4())
    run_dir = Path(base_dir) / ".runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def list_run_dirs(base_dir: Path | str) -> List[Path]:
    runs_dir = Path(base_dir) / ".runs"
    if not runs_dir.exists():
        return []
    return sorted([path for path in runs_dir.iterdir() if path.is_dir()], key=lambda path: path.stat().st_mtime, reverse=True)


def prune_run_dirs(base_dir: Path | str, *, keep: int) -> List[Path]:
    run_dirs = list_run_dirs(base_dir)
    if keep < 0:
        keep = 0
    to_remove = run_dirs[keep:]
    removed: List[Path] = []
    for path in to_remove:
        shutil.rmtree(path, ignore_errors=False)
        removed.append(path)
    return removed


def write_meta(run_dir: Path, meta: Dict[str, Any]) -> None:
    """Writes the metadata dictionary to the run directory as JSON."""
    if "git_commit" not in meta or not meta["git_commit"]:
        meta["git_commit"] = get_git_commit()
    if "created_at" not in meta:
        meta["created_at"] = datetime.now(timezone.utc).isoformat()
    if "run_id" not in meta:
        meta["run_id"] = run_dir.name

    meta_path = run_dir / "meta.json"
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
