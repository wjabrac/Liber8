#!/usr/bin/env python3
"""LIBR8 Voice Control — Click-to-Talk GUI.

No wake word needed. Press the button, speak, release; the command runs.
Requires only: tkinter (stdlib), sounddevice (already installed), vosk (already installed).
Run from the LIBR8 project root:
    python3 run_voice_gui.py
"""

import sys
import threading
import queue
import json
import os
import tkinter as tk
from tkinter import scrolledtext
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
MODEL_PATH = ROOT / "model"

# ── Audio settings ────────────────────────────────────────────────────────────
SAMPLE_RATE  = 16000
BLOCK_SIZE   = 4096
MAX_SILENCE  = 20   # chunks of silence before auto-stop (~5 sec)


# ── Core STT (runs in a background thread) ───────────────────────────────────

def transcribe_once(log_fn) -> str:
    """Record until silence; return the transcribed text. Blocking."""
    try:
        import sounddevice as sd
        import vosk
    except ImportError as e:
        log_fn(f"[ERROR] Missing library: {e}")
        return ""

    if not MODEL_PATH.exists():
        log_fn(f"[ERROR] Vosk model not found at {MODEL_PATH}")
        log_fn("Download from https://alphacephei.com/vosk/models and extract as 'model/'")
        return ""

    vosk.SetLogLevel(-1)
    model = vosk.Model(str(MODEL_PATH))
    rec   = vosk.KaldiRecognizer(model, SAMPLE_RATE)

    audio_q: queue.Queue[bytes] = queue.Queue()

    def _cb(indata, frames, time_info, status):
        audio_q.put(bytes(indata))

    text_parts: list[str] = []
    silence_count = 0

    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
                           dtype="int16", channels=1, callback=_cb):
        while True:
            data = audio_q.get()
            if rec.AcceptWaveform(data):
                chunk = json.loads(rec.Result()).get("text", "").strip()
                if chunk:
                    text_parts.append(chunk)
                    silence_count = 0
                else:
                    silence_count += 1
            else:
                partial = json.loads(rec.PartialResult()).get("partial", "")
                silence_count = 0 if partial else silence_count + 1

            if silence_count >= MAX_SILENCE:
                break

    return " ".join(text_parts).strip()


# ── Route to CognitionEngine ─────────────────────────────────────────────────

def run_command(text: str, log_fn) -> None:
    """Feed the transcribed text into LIBR8's CognitionEngine."""
    try:
        from src.cognition.engine import CognitionEngine
        engine = CognitionEngine(base_storage_dir=str(ROOT / ".runs"), fallback_mode=True)
        record = engine.run(text)
        
        if record.tool_calls:
            for call in record.tool_calls:
                name = call.get("name")
                args = call.get("arguments", {})
                log_fn(f"[TOOL] Executed {name}({args})")
                # Show the output of the tool call if available from provenance
                summary = record.provenance.get("output_summary", "")
                if summary:
                    log_fn(f"       Result: {summary}")
        else:
            log_fn(f"[*] Engine outcome: {record.outcome}")
            
    except Exception as exc:
        log_fn(f"[-] Engine error: {exc}")


# ── GUI ───────────────────────────────────────────────────────────────────────

class VoiceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LIBR8 Voice Control")
        self.resizable(False, False)
        self.configure(bg="#111827")

        # ── Status label ─────────────────────────────────────────────────────
        self._status_var = tk.StringVar(value="Ready")
        lbl = tk.Label(self, textvariable=self._status_var,
                       font=("Helvetica", 13, "bold"),
                       bg="#111827", fg="#9ca3af")
        lbl.pack(pady=(20, 5))

        # ── Big record button ─────────────────────────────────────────────────
        self._btn = tk.Button(
            self, text="🎙  Hold to Record",
            font=("Helvetica", 16, "bold"),
            bg="#2563eb", fg="white",
            activebackground="#1d4ed8", activeforeground="white",
            relief="flat", bd=0,
            padx=32, pady=18,
            cursor="hand2",
            command=self._on_click,
        )
        self._btn.pack(padx=40, pady=10)

        # ── Log area ─────────────────────────────────────────────────────────
        self._log = scrolledtext.ScrolledText(
            self, width=60, height=14,
            font=("Courier", 10),
            bg="#1f2937", fg="#e5e7eb",
            insertbackground="white",
            relief="flat", bd=0,
            state="disabled",
        )
        self._log.pack(padx=20, pady=(0, 20))

        self._recording = False

    def _log_msg(self, msg: str) -> None:
        def _inner():
            self._log.config(state="normal")
            self._log.insert(tk.END, msg.rstrip("\n") + "\n")
            self._log.see(tk.END)
            self._log.config(state="disabled")
        self.after(0, _inner)

    def _set_status(self, text: str, color: str = "#9ca3af") -> None:
        def _inner():
            self._status_var.set(text)
            self._status_var  # force repaint
        self.after(0, _inner)

    def _on_click(self) -> None:
        if self._recording:
            return  # ignore double-clicks while already recording
        self._recording = True
        self._btn.config(bg="#dc2626", text="🔴  Listening…")
        self._status_var.set("Listening…")
        threading.Thread(target=self._record_and_run, daemon=True).start()

    def _record_and_run(self) -> None:
        self._log_msg("\n--- Recording ---")
        text = transcribe_once(self._log_msg)

        if text:
            self._log_msg(f"[YOU]: {text}")
            self._log_msg("[*] Running command...")
            run_command(text, self._log_msg)
        else:
            self._log_msg("[-] Nothing detected.")

        # Reset button
        self.after(0, lambda: self._btn.config(bg="#2563eb", text="🎙  Hold to Record"))
        self.after(0, lambda: self._status_var.set("Ready"))
        self._recording = False


if __name__ == "__main__":
    app = VoiceApp()
    app.mainloop()
