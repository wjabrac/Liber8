"""Minimal CLI for running the cognition router."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from .contracts import EventRecord
from .eventlog import EventLog
from .orchestration.router import run_router


def _default_run_dir() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(".runs") / timestamp


def _read_latest_events(paths: Iterable[Path]) -> list[EventRecord]:
    events: list[EventRecord] = []
    for path in paths:
        if not path.exists():
            continue
        log = EventLog(path)
        records = log.read_all()
        if records:
            events.append(records[-1])
    return events


def _find_run_dirs(base_dir: Path, limit: int) -> list[Path]:
    if not base_dir.exists():
        return []
    run_dirs = [path for path in base_dir.iterdir() if path.is_dir()]
    run_dirs.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return run_dirs[:limit]


def run_command(args: argparse.Namespace) -> int:
    storage_dir = Path(args.storage) if args.storage else _default_run_dir()
    storage_dir.mkdir(parents=True, exist_ok=True)
    event = run_router(
        args.task,
        storage_dir,
        fake_backend=args.fake,
        model_endpoint=args.model_endpoint,
    )
    if args.print_json:
        print(json.dumps(event.to_dict()))
    else:
        print(f"{event.id} {event.outcome} {storage_dir}")
    return 0


def show_runs_command(args: argparse.Namespace) -> int:
    base_dir = Path(args.storage) if args.storage else Path(".runs")
    run_dirs = _find_run_dirs(base_dir, args.limit)
    event_logs = [run_dir / "eventlog.jsonl" for run_dir in run_dirs]
    events = _read_latest_events(event_logs)
    for event, run_dir in zip(events, run_dirs):
        print(f"{event.id} {event.outcome} {run_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="liber8")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a task")
    run_parser.add_argument("task", help="Task string")
    run_parser.add_argument("--storage", help="Storage directory path")
    run_parser.add_argument("--fake", action="store_true", help="Use fake backend")
    run_parser.add_argument("--model-endpoint", help="Model endpoint URL")
    run_parser.add_argument("--print-json", action="store_true", help="Print full EventRecord JSON")
    run_parser.set_defaults(func=run_command)

    show_parser = subparsers.add_parser("show-runs", help="List latest runs")
    show_parser.add_argument("--storage", help="Base storage directory")
    show_parser.add_argument("--limit", type=int, default=5, help="Number of runs to list")
    show_parser.set_defaults(func=show_runs_command)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
