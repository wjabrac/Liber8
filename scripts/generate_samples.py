import os
import shutil
from pathlib import Path
from src.cognition.config import EngineConfig
from src.cognition.engine import CognitionEngine

def main():
    base_dir = Path("specimens")
    if base_dir.exists():
        shutil.rmtree(base_dir)
    base_dir.mkdir()
    
    # 1. Fallback mode
    fb_dir = base_dir / "fallback_run"
    fb_config = EngineConfig(cognition_backend="fallback")
    fb_engine = CognitionEngine(fb_config)
    fb_engine.run("Generate fallback sample", fb_dir)
    print("Fallback run generated.")
    
    # 2. DSPy mode
    dspy_dir = base_dir / "dspy_run"
    dspy_config = EngineConfig(cognition_backend="dspy+zep")
    dspy_engine = CognitionEngine(dspy_config)
    dspy_engine.run("Generate dspy+zep sample", dspy_dir)
    print("DSPy+Zep run generated.")

if __name__ == "__main__":
    main()
