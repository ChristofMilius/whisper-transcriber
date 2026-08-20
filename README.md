# Whisper Transcriber

CLI tool to transcribe video/audio files using OpenAI Whisper (turbo model).

## Features

- Transcribe video and audio files to text
- Optional VTT subtitle output with timestamps
- GUI file dialogs (tkinter) with manual fallback
- WSL2 path conversion support
- Custom model loading from local `models/` directory
- Graceful signal handling (Ctrl+C)

## Requirements

- Python 3.13+
- ffmpeg on PATH

## Installation

```bash
uv sync
```

## Usage

```bash
uv run whisper_transcriber_turbo_hardened.py
```

## Supported Formats

mp4, mp3, m4a, wav, webm, ogg, flac, mkv, avi, mov

## Notes

- Model weights are stored in `models/` (gitignored due to size)
- GPU acceleration via CUDA when available
