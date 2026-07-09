# whisper-dictation
[![ci](https://github.com/theautomatist/whisper-dictation/actions/workflows/ci.yml/badge.svg)](https://github.com/theautomatist/whisper-dictation/actions/workflows/ci.yml)

Local, private push-to-talk dictation for Windows — powered by
[faster-whisper](https://github.com/SYSTRAN/faster-whisper) `large-v3` running
on your own GPU. Hold a key, speak, release: the transcribed text is typed at
your cursor. No cloud, no account, nothing leaves your machine.

Think of it as a local, offline Wispr Flow.

## How it works

1. Hold **CTRL + Windows** and speak.
2. Release the keys — the audio is transcribed on the GPU and pasted at the cursor.
3. Press **Shift+Tab** (while the dictation window is focused) to switch the
   paste shortcut between **CTRL+V** and **CTRL+SHIFT+V** — handy because most
   terminals only paste with CTRL+SHIFT+V.
4. Press **ESC** (with the dictation window focused) to quit.

The model runs in int8 and fits comfortably in ~6 GB of VRAM. On a modern GPU,
transcription is several times faster than real time.

## Quick start

```bat
python -m venv venv
venv\Scripts\pip install -r requirements.txt
start-dictation.bat
```

The first run downloads the model (~3 GB) from HuggingFace automatically.
See **[SETUP.md](SETUP.md)** for the full guide — CUDA/GPU notes, microphone
selection, CPU fallback, and troubleshooting.

## Files

| File | Purpose |
|------|---------|
| `dictate.py` | The dictation tool (main program). |
| `start-dictation.bat` | Double-click launcher for `dictate.py`. |
| `mic_test.py` / `test-microphone.bat` | Check which microphone delivers signal. |
| `test_engine.py` | Verify the model loads and CUDA acceleration works. |
| `hotkey_test.py` | Diagnose the global keyboard hook and key names. |
| `download_loop.sh` | Optional resilient model download for flaky networks. |

## Notes

- **Windows only.** Uses the Windows clipboard, `os.add_dll_directory`, and the
  Windows-key scan codes.
- The default recognition language is German (`LANGUAGE = "de"` in
  `dictate.py`); set it to your language code or `None` for auto-detect.
- The `keyboard` library installs a global hook. Run the tool from a terminal
  started **as administrator** so the hotkeys are captured in every app.
- Works without a GPU too — it falls back to CPU (`int8`), just slower.

## License

MIT — see [LICENSE](LICENSE).
