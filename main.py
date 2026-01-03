"""Run a minimal cognition loop with fake backend."""

from __future__ import annotations

from pathlib import Path

from src.cognition_loop import run_cognition_loop


def main() -> None:
    run_dir = Path(".runs")
    run_dir.mkdir(parents=True, exist_ok=True)
    event = run_cognition_loop("run cognition loop", run_dir, fake_backend=True)
    print(f"Event ID: {event.id}")
    print(f"Event log: {run_dir / 'eventlog.jsonl'}")
    print(f"Memory log: {run_dir / 'memory.jsonl'}")


if __name__ == "__main__":
    main()
