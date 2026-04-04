"""Executable script to start the LIBR8 Voice Daemon."""
import argparse
from src.voice.daemon import VoiceGate, Transcriber
from src.cognition.engine import CognitionEngine
from src.tools.disk_cleanup import DiskScanner, execute_plan

# Keywords that trigger disk cleanup planning (plan-only; no args passed to execute)
_CLEANUP_KEYWORDS = [
    "clean", "cleanup", "clean up", "disk cleanup", "free space",
    "clear cache", "delete cache", "remove junk", "tidy", "disk space",
]

def process_voice_command(text: str, engine: CognitionEngine):
    """Routes a transcribed command to the correct handler."""
    if not text:
        return

    print(f"\n[RECEIVED COMMAND]: {text}")
    text_lower = text.lower()

    # -- Disk cleanup planning intent --
    if any(kw in text_lower for kw in _CLEANUP_KEYWORDS):
        print("[*] Disk cleanup intent detected. Scanning (read-only)...")
        scanner = DiskScanner(scan_root="~")
        plan = scanner.scan()
        print("\n" + plan.summary())
        print("\n[*] Plan presented. No files were deleted.")
        print("[*] To execute, call execute_plan(plan, confirmed=True) from Python.")
        return

    # -- General command via CognitionEngine --
    print("[*] Passing to CognitionEngine...")
    try:
        record = engine.run(text)
        print(f"[*] Command processed. Outcome: {record.outcome}")
    except Exception as e:
        print(f"[-] Engine failed to process command: {e}")

def main():
    parser = argparse.ArgumentParser(description="LIBR8 Voice Control Daemon")
    parser.add_argument("--wake", type=str, default="rig", help="Wake word (default: rig)")
    parser.add_argument("--model", type=str, default="model", help="Path to Vosk model directory")
    parser.add_argument("--storage", type=str, default=".runs", help="Storage directory for the engine")
    args = parser.parse_args()

    engine = CognitionEngine(base_storage_dir=args.storage, fallback_mode=True)
    gate = VoiceGate(wake_word=args.wake, model_path=args.model)
    # Transcriber shares the already-loaded Vosk model — zero extra disk cost
    transcriber = Transcriber(gate=gate)

    def on_wake_detected():
        command_text = transcriber.record_and_transcribe()
        process_voice_command(command_text, engine)

    try:
        gate.start_listening(on_wake_detected)
    except KeyboardInterrupt:
        print("\n[*] Shutting down voice daemon.")
        gate.stop()

if __name__ == "__main__":
    main()
