# Whisper Transcriber

CLI tool to transcribe video/audio files using OpenAI Whisper (turbo model).

## Features

- Transcribe video and audio files to text
- Optional VTT subtitle output with timestamps
- GUI file dialogs (tkinter) with manual fallback
- WSL2 path conversion support
- Graceful signal handling (Ctrl+C)
- GPU acceleration via CUDA (automatic, CPU fallback)

## Requirements

- Python 3.13+
- ffmpeg on PATH

## Installation

```bash
uv sync
```

## GPU Acceleration (CUDA)

The tool automatically runs on CUDA when available and falls back to CPU otherwise (fp16 is enabled on CUDA).

### Prerequisites

- NVIDIA GPU
- NVIDIA driver supporting CUDA 12.8 or newer — verify with:

```bash
nvidia-smi
```

### Setup

`uv sync` installs the CUDA build of PyTorch automatically: `pyproject.toml`
pins torch to PyTorch's official CUDA 12.8 wheel index (`pytorch-cu128`) via
`[tool.uv.sources]`, so no extra steps are required.

To switch to a different CUDA version, update the index URL in `pyproject.toml`
(e.g. `.../whl/cu126`) and re-run `uv sync`.

### Verify

```bash
uv run python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu')"
```

Prints `True <GPU name>` when GPU acceleration is active; `False cpu` means transcription runs on CPU.

## Model Weights

The tool always loads the **turbo** model (`large-v3-turbo`, ~1.6 GB) through Whisper's standard
model resolution:

1. **User cache** — if the checkpoint already exists in `~/.cache/whisper/` (Windows:
   `%USERPROFILE%\.cache\whisper`, override via `XDG_CACHE_HOME`), it is loaded from there.
2. **Auto-download** — otherwise it is downloaded on first run into that cache (~1.6 GB, one time)
   and reused for every subsequent launch.

No manual setup is required: launch once and let Whisper fetch the checkpoint automatically.
If you manage the weights yourself (e.g. offline machines), place a downloaded
`large-v3-turbo.pt` into the cache directory shown above.

## Usage

```bash
uv run whisper_transcriber_turbo_hardened.py
```

## Supported Formats

mp4, mp3, m4a, wav, webm, ogg, flac, mkv, avi, mov

## License

MIT

## Notes

- Model weights: see [Model Weights](#model-weights) (stored in Whisper's user cache, not in the repo)
- Output files are written unconditionally — existing `_transcript.txt` / `.vtt` files are overwritten without confirmation
- GPU acceleration: see [GPU Acceleration (CUDA)](#gpu-acceleration-cuda)
