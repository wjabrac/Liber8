"""Run state tracking for crash safety."""
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict
from pathlib import Path

@dataclass
class RunState:
    task: str = ""
    status: str = "pending"
    current_step: int = 1
    attempt: int = 1
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    def save(self, run_dir: Path) -> None:
        run_dir.mkdir(parents=True, exist_ok=True)
        state_file = run_dir / "run_state.json"
        tmp_file = run_dir / "run_state.json.tmp"
        with open(tmp_file, "w") as f:
            json.dump(asdict(self), f, indent=2)
        os.replace(tmp_file, state_file)
        
    @classmethod
    def load(cls, run_dir: Path) -> "RunState":
        state_file = run_dir / "run_state.json"
        if not state_file.exists():
            return cls()
        with open(state_file, "r") as f:
            data = json.load(f)
        return cls(**data)
