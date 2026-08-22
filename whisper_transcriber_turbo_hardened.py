#!/usr/bin/env python3
"""
whisper_transcribe.py
---------------------.
CLI tool to transcribe a video/audio file using OpenAI Whisper (turbo model).
Works on Windows and WSL2 (requires tkinter + X server for GUI dialogs,
falls back to manual path input if unavailable).

Dependencies:
    uv sync  (installs openai-whisper + torch with CUDA support from the pinned cu128 index)
    ffmpeg must be on PATH
"""

import os
import sys
import signal
import textwrap
from typing import Optional, Tuple

# Core dependencies
try:
    import whisper
except ImportError:
    print("\n  [!] openai-whisper is not installed.")
    print("      Run:  uv sync")
    sys.exit(1)

try:
    import torch
except ImportError:
    print("\n  [!] torch is not installed.")
    print("      Run:  uv sync")
    sys.exit(1)

try:
    import tkinter as tk
    from tkinter import filedialog
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

# Platform-specific imports
if os.name == 'posix':
    import fcntl
    import termios

# Signal handling
shutdown_requested = False

def signal_handler(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    print(f"\n\n  [!] Received signal {signum}. Shutting down gracefully...")
    sys.exit(0)

# Register signal handlers based on platform
if os.name == 'posix':
    # Unix-like systems (Linux, macOS)
    signal.signal(signal.SIGINT, signal_handler)     # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)   # Termination request
    signal.signal(signal.SIGHUP, signal_handler)    # Terminal closed
else:
    # Windows systems
    signal.signal(signal.SIGINT, signal_handler)     # Ctrl+C/Ctrl+Break

# Helpers
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    print("=" * 60)
    print("  Whisper Transcriber  |  turbo model")
    print("=" * 60)
    print()

def pick_file_dialog(title, filetypes):
    """Open a tkinter file dialog, hide the root window."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()
    return path or None

def pick_save_dialog(title, defaultextension, filetypes):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.asksaveasfilename(
        title=title,
        defaultextension=defaultextension,
        filetypes=filetypes,
    )
    root.destroy()
    return path or None

def pick_dir_dialog(title):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askdirectory(title=title)
    root.destroy()
    return path or None

def prompt_path(prompt_text):
    """Manual fallback when tkinter is unavailable."""
    raw = input(f"{prompt_text}\n> ").strip().strip('"').strip("'")
    return raw if raw else None

def resolve_wsl_path(path):
    """
    If running in WSL and the user pastes a Windows path (C:\\...),
    convert it to /mnt/c/... format.
    """
    if os.name != "nt" and len(path) >= 2 and path[1] == ":":
        drive = path[0].lower()
        rest = path[2:].replace("\\", "/")
        return f"/mnt/{drive}{rest}"
    return path

def validate_input_file(path):
    path = resolve_wsl_path(path)
    if not os.path.isfile(path):
        print(f"\n  [!] File not found: {path}")
        return None
    ext = os.path.splitext(path)[1].lower()
    allowed = {".mp4", ".mp3", ".m4a", ".wav", ".webm", ".ogg", ".flac", ".mkv", ".avi", ".mov"}
    if ext not in allowed:
        print(f"\n  [!] Extension '{ext}' not in supported list: {', '.join(sorted(allowed))}")
        print("      Proceeding anyway — Whisper will try via ffmpeg.")
    return path

# Menu steps
def step_select_input():
    print("  STEP 1 — Select input file")
    print()
    if TK_AVAILABLE:
        print("  [1] Open file dialog")
        print("  [2] Enter path manually")
        print()
        choice = input("  Choice: ").strip()
    else:
        print("  (tkinter not available — manual input only)")
        choice = "2"

    if choice == "1":
        path = pick_file_dialog(
            title="Select video or audio file",
            filetypes=[
                ("Media files", "*.mp4 *.mp3 *.m4a *.wav *.webm *.ogg *.flac *.mkv *.avi *.mov"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            print("\n  [!] No file selected.")
            return None
    else:
        path = prompt_path("  Paste full path to the media file:")
        if not path:
            return None

    return validate_input_file(path)

def step_select_output(input_path, want_vtt):
    print()
    print("  STEP 2 — Select output location")
    print()

    default_stem = os.path.splitext(os.path.basename(input_path))[0]
    default_txt  = default_stem + "_transcript.txt"
    default_vtt  = default_stem + "_transcript.vtt"

    if TK_AVAILABLE:
        print("  [1] Choose output folder (files named automatically)")
        print("  [2] Choose output .txt file explicitly")
        print("  [3] Use same folder as input file")
        print()
        choice = input("  Choice: ").strip()
    else:
        print("  (tkinter not available — manual input only)")
        choice = "3"

    if choice == "1":
        folder = pick_dir_dialog("Select output folder")
        if not folder:
            print("\n  [!] No folder selected.")
            return None, None
        txt_path = os.path.join(folder, default_txt)
        vtt_path = os.path.join(folder, default_vtt) if want_vtt else None

    elif choice == "2":
        txt_path = pick_save_dialog(
            title="Save transcript as…",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not txt_path:
            print("\n  [!] No file selected.")
            return None, None
        folder   = os.path.dirname(txt_path)
        vtt_path = os.path.join(folder, default_vtt) if want_vtt else None

    else:  # same folder as input
        folder   = os.path.dirname(os.path.abspath(input_path))
        txt_path = os.path.join(folder, default_txt)
        vtt_path = os.path.join(folder, default_vtt) if want_vtt else None

    return txt_path, vtt_path

def step_options():
    print()
    print("  STEP 3 — Options")
    print()
    print("  Model     : turbo  (fixed)")
    print()

    lang = input("  Language  [en]: ").strip().lower() or "en"

    vtt_ans = input("  Also save .vtt with timestamps? [y/N]: ").strip().lower()
    want_vtt = vtt_ans in ("y", "yes")

    return lang, want_vtt

# Transcription
def run_transcription(input_path: str, txt_path: str, vtt_path: Optional[str], language: str) -> bool:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    fp16   = device == "cuda"

    print()
    print(f"  Loading model turbo on {device.upper()} …")
    try:
        model = whisper.load_model("turbo", device=device)
    except Exception as e:
        print(f"\n  [!] Failed to load model: {e}")
        return False

    print(f"  Transcribing : {os.path.basename(input_path)}")
    print(f"  Device       : {device.upper()}  |  fp16: {fp16}")
    print()

    try:
        result = model.transcribe(
            input_path,
            language=language,
            verbose=False,
            fp16=fp16,
        )
    except Exception as e:
        print(f"\n  [!] Transcription failed: {e}")
        return False

    # Plain text
    os.makedirs(os.path.dirname(os.path.abspath(txt_path)), exist_ok=True)
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(result["text"].strip())
        print(f"  ✓ Transcript saved : {txt_path}")
    except Exception as e:
        print(f"\n  [!] Failed to save transcript: {e}")
        return False

    # VTT (optional)
    if vtt_path:
        def fmt_ts(seconds):
            h  = int(seconds // 3600)
            m  = int((seconds % 3600) // 60)
            s  = int(seconds % 60)
            ms = int((seconds % 1) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

        try:
            with open(vtt_path, "w", encoding="utf-8") as f:
                f.write("WEBVTT\n\n")
                for i, seg in enumerate(result["segments"], 1):
                    f.write(f"{i}\n")
                    f.write(f"{fmt_ts(seg['start'])} --> {fmt_ts(seg['end'])}\n")
                    f.write(seg["text"].strip() + "\n\n")
            print(f"  ✓ VTT saved        : {vtt_path}")
        except Exception as e:
            print(f"\n  [!] Failed to save VTT: {e}")

    return True

# Main menu loop
def main_menu():
    while not shutdown_requested:
        clear()
        banner()
        print("  MAIN MENU")
        print()
        print("  [1] Transcribe a file")
        print("  [q] Quit")
        print()
        choice = input("  Choice: ").strip().lower()

        if choice == "1":
            transcribe_flow()
        elif choice in ("q", "quit", "exit"):
            print("\n  Bye.\n")
            break
        else:
            print("\n  Unknown option.")
            input("  Press Enter to continue…")

def transcribe_flow():
    clear()
    banner()

    # Step 1 — input
    input_path = step_select_input()
    if not input_path:
        input("\n  Press Enter to return to menu…")
        return

    # Step 3 — options (before output so we know want_vtt)
    language, want_vtt = step_options()

    # Step 2 — output
    txt_path, vtt_path = step_select_output(input_path, want_vtt)
    if not txt_path:
        input("\n  Press Enter to return to menu…")
        return

    # Confirm
    print()
    print("  ── Summary ──────────────────────────────────────")
    print(f"  Input    : {input_path}")
    print(f"  Output   : {txt_path}")
    if vtt_path:
        print(f"  VTT      : {vtt_path}")
    print(f"  Language : {language}")
    print()
    go = input("  Start transcription? [Y/n]: ").strip().lower()
    if go in ("n", "no"):
        return

    print()
    ok = run_transcription(input_path, txt_path, vtt_path, language)

    if ok:
        print()
        print("  Done.")
    input("\n  Press Enter to return to menu…")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n  [!] Interrupted by user. Exiting...")
        sys.exit(0)
