# Setup guide

Step-by-step setup for **whisper-dictation** on Windows.

## 1. Requirements

| | |
|---|---|
| **OS** | Windows 10 / 11 (the tool is Windows-only). |
| **Python** | 3.10 (developed on 3.10.2). 3.9–3.12 should also work. |
| **GPU** *(recommended)* | NVIDIA GPU with a recent driver (CUDA 12). ~6 GB VRAM is enough for `large-v3` in int8. |
| **Disk** | ~3 GB for the model + ~3 GB for the virtual environment. |
| **Microphone** | Any input device Windows recognizes. |

No GPU? The tool still runs — it automatically falls back to CPU (`int8`),
which is slower but works. See [CPU-only install](#cpu-only-install).

## 2. Get the code

```bat
git clone https://github.com/theautomatist/whisper-dictation.git
cd whisper-dictation
```

## 3. Create the virtual environment and install dependencies

```bat
python -m venv venv
venv\Scripts\pip install --upgrade pip
venv\Scripts\pip install -r requirements.txt
```

This pulls in faster-whisper, sounddevice, keyboard, pyperclip, numpy, and the
CUDA 12 runtime libraries (`nvidia-cublas-cu12`, `nvidia-cudnn-cu12`) that the
scripts load explicitly.

## 4. Verify microphone and engine

**Microphone** — records 6 seconds and prints the input level:

```bat
venv\Scripts\python mic_test.py          :: default mic
venv\Scripts\python mic_test.py list     :: list all devices with their index
venv\Scripts\python mic_test.py 3        :: test a specific device index
```

If you see `NO SIGNAL`, pick a different index and set it as `MIC_DEVICE` in
`dictate.py`.

**Engine** — loads the model and transcribes the bundled `jfk.wav`. The first
run downloads the model (~3 GB) from HuggingFace:

```bat
venv\Scripts\python test_engine.py
```

A healthy run reports something like `... 8.0x real-time` and prints the
transcript. If it says `GPU init failed -> falling back to CPU`, jump to
[Troubleshooting](#troubleshooting).

## 5. Run it

```bat
start-dictation.bat
```

or directly:

```bat
venv\Scripts\python dictate.py
```

Then:

- **Hold CTRL + Windows**, speak, and **release** — the text is pasted at your cursor.
- **Shift+Tab** (dictation window focused) toggles the paste shortcut
  **CTRL+V ↔ CTRL+SHIFT+V**.
- **ESC** (dictation window focused) quits.

> **Run as administrator** for reliable global hotkeys. The `keyboard` library
> installs a low-level hook; without elevation, key presses in some apps
> (anything running elevated) are not seen.

## Configuration

All settings live at the top of `dictate.py`:

| Setting | Meaning |
|---------|---------|
| `LANGUAGE` | Recognition language, e.g. `"de"`, `"en"`. `None` = auto-detect (a bit slower). |
| `MIC_DEVICE` | `None` = Windows default mic, or a device index from `mic_test.py list`. |
| `MODEL` | Auto-detects a local `models/large-v3/model.bin`, otherwise downloads `large-v3`. |
| `DEVICE` / `COMPUTE` | `"cuda"` / `"int8_float16"`. For CPU set `COMPUTE = "int8"`. |
| `PASTE_MODES` | The two paste shortcuts cycled by Shift+Tab. Default starts at `CTRL+V`. |
| `MIN_SECONDS` | Recordings shorter than this are ignored. |

## CPU-only install

If you have no NVIDIA GPU:

1. Remove the two `nvidia-*` lines from `requirements.txt` before installing.
2. In `dictate.py` set `COMPUTE = "int8"` (or just let the automatic CPU
   fallback handle it).

Transcription will be noticeably slower but fully functional.

## Optional: pre-download the model on a flaky connection

faster-whisper downloads the model automatically on first run. If your
connection drops often, `download_loop.sh` (Git Bash) fetches `model.bin` with
patient, resumable retries into `models/large-v3/`.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `GPU init failed` / falls back to CPU | Update your NVIDIA driver; confirm `nvidia-cublas-cu12` and `nvidia-cudnn-cu12` are installed in the venv. A CUDA 12-capable driver is required. |
| Hotkeys do nothing | Run the terminal / `.bat` **as administrator**. Verify the hook with `venv\Scripts\python hotkey_test.py`. |
| `NO SIGNAL` from the mic | Wrong or muted device. Use `mic_test.py list`, then set `MIC_DEVICE`. |
| Text pasted but not visible in a terminal | Toggle paste mode with **Shift+Tab** (many terminals need CTRL+SHIFT+V). |
| Windows key not detected | Handled via scan codes (91/92). Run `hotkey_test.py` to inspect key names on your locale. |
| ESC / Shift+Tab ignored | They only fire while the dictation window is focused (by design, so they stay usable elsewhere). |
