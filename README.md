# Whisper Transcriber

CLI tool to transcribe video/audio files using OpenAI Whisper (turbo model).

## Features

- Transcribe video and audio files to text
- Optional VTT subtitle output with timestamps
- GUI file dialogs (tkinter) with manual fallback
- WSL2 path conversion support
- Custom model loading from local `models/` directory
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

## Usage

```bash
uv run whisper_transcriber_turbo_hardened.py
```

## Supported Formats

mp4, mp3, m4a, wav, webm, ogg, flac, mkv, avi, mov

## License

MIT

## Notes

- Model weights are stored in `models/` (gitignored due to size)
- GPU acceleration: see [GPU Acceleration (CUDA)](#gpu-acceleration-cuda)
