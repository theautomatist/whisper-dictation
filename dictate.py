"""
Local dictation with faster-whisper large-v3 (int8) on the GPU.
Works like Wispr Flow: hold a key, speak, release -> text appears at the cursor.

Usage:
    Hold CTRL + WINDOWS, speak, then release.
    The recognized text is inserted at the cursor via the clipboard.
    SHIFT+TAB (while the dictation window is focused) toggles the paste mode:
        CTRL+V  <->  CTRL+SHIFT+V  (terminals often need CTRL+SHIFT+V).
    ESC quits the program (only when the dictation window is focused).

Run:
    venv/Scripts/python.exe dictate.py
"""
import os
import sys
import time
import queue
import threading
import ctypes

# --- Make the CUDA DLLs from the pip packages discoverable ---
def _add_cuda_dlls():
    base = os.path.join(sys.prefix, "Lib", "site-packages", "nvidia")
    for sub in ("cublas", "cudnn"):
        p = os.path.join(base, sub, "bin")
        if os.path.isdir(p):
            os.add_dll_directory(p)

_add_cuda_dlls()

import numpy as np
import sounddevice as sd
import keyboard
import pyperclip
from faster_whisper import WhisperModel

# Give this console a stable title so the focus-bound ESC / Shift+Tab below work
# even when launched directly with `python dictate.py`, not only via the .bat.
WINDOW_TITLE = "Local Dictation (Whisper large-v3)"
try:
    ctypes.windll.kernel32.SetConsoleTitleW(WINDOW_TITLE)
except Exception:
    pass

# ----------------------------- Configuration -----------------------------
# Trigger: hold CTRL + WINDOWS (logic in on_event() below).
LANGUAGE = "de"           # fixed language saves time; None = auto-detect
MIC_DEVICE = None         # None = Windows default mic; otherwise device index (see mic_test.py list)
_HERE = os.path.dirname(os.path.abspath(__file__))
_local = os.path.join(_HERE, "models", "large-v3")
MODEL = _local if os.path.isfile(os.path.join(_local, "model.bin")) else "large-v3"
DEVICE = "cuda"
COMPUTE = "int8_float16"
SAMPLE_RATE = 16000
MIN_SECONDS = 0.3         # ignore shorter recordings
# Paste shortcuts, switchable with Shift+Tab (see below).
# CTRL+V for normal programs; CTRL+SHIFT+V for terminals (Windows Terminal,
# VS Code, many Linux terminals) that only paste from the clipboard that way.
PASTE_MODES = ["ctrl+v", "ctrl+shift+v"]
_paste_mode = 0           # index into PASTE_MODES; toggled via Shift+Tab
# -------------------------------------------------------------------------

print(f"Loading model '{MODEL}' ({COMPUTE}) on {DEVICE} ...")
t0 = time.time()
try:
    model = WhisperModel(MODEL, device=DEVICE, compute_type=COMPUTE)
except Exception as e:
    print(f"[!] GPU init failed: {e}\n    -> falling back to CPU (int8)")
    model = WhisperModel(MODEL, device="cpu", compute_type="int8")
print(f"Model ready in {time.time() - t0:.1f}s")

_mic = sd.query_devices(MIC_DEVICE if MIC_DEVICE is not None else sd.default.device[0])
print(f"Microphone: {_mic['name']}  (index {sd.default.device[0] if MIC_DEVICE is None else MIC_DEVICE})")
print("  -> wrong mic? Set 'MIC_DEVICE' in dictate.py (index via mic_test.py list)\n")

print("=" * 60)
print(f"  Hold [CTRL] + [WINDOWS] and speak.")
print(f"  Release      -> text is inserted at the cursor.")
print(f"  [SHIFT+TAB]  -> paste mode CTRL+V <-> CTRL+SHIFT+V")
print(f"                 (current: {PASTE_MODES[_paste_mode].upper()})")
print(f"  [ESC]        -> quit.")
print("=" * 60 + "\n")

_frames = []
_stream = None
_recording = False
_jobs: "queue.Queue" = queue.Queue()


def _callback(indata, frames, time_info, status):
    if status:
        # e.g. overflow -- not critical
        pass
    _frames.append(indata.copy())


def start_recording():
    global _stream, _frames, _recording
    _frames = []
    try:
        _stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="float32",
            device=MIC_DEVICE, callback=_callback
        )
        _stream.start()
        print("  ... recording ...", end="\r", flush=True)
    except Exception as ex:
        _recording = False
        _stream = None
        print(f"  (!) Could not open the microphone: {ex}")
        print("      Is another dictation window already running? If so, close this one.")


def stop_recording():
    global _stream
    if _stream is not None:
        _stream.stop()
        _stream.close()
        _stream = None
    if not _frames:
        return
    audio = np.concatenate(_frames, axis=0).flatten()
    if len(audio) < SAMPLE_RATE * MIN_SECONDS:
        print("  (too short, ignored)        ")
        return
    peak = float(np.abs(audio).max()) if len(audio) else 0.0
    if peak < 0.01:
        print(f"  (!) No signal from the microphone (level {peak:.3f}). Wrong/muted mic?")
        print("      -> run mic_test.py to check, then set MIC_DEVICE in dictate.py.")
        return
    _jobs.put(audio)


def worker():
    while True:
        audio = _jobs.get()
        if audio is None:
            return
        print("  ... transcribing ...        ", end="\r", flush=True)
        t = time.time()
        segments, info = model.transcribe(audio, language=LANGUAGE, beam_size=5)
        text = " ".join(s.text.strip() for s in segments).strip()
        dt = time.time() - t
        if text:
            pyperclip.copy(text + " ")
            keyboard.send(PASTE_MODES[_paste_mode])
            print(f"  [{dt:.1f}s] {text}")
        else:
            print("  (nothing recognized)            ")


def _is_pressed(name):
    try:
        return keyboard.is_pressed(name)
    except Exception:
        return False


# Query the Windows key via scan code (91 = left, 92 = right).
# Needed because keyboard.is_pressed("windows") fails on a German locale
# (the key is internally called 'linke windows' there). Ctrl works by name.
def on_event(_e):
    global _recording
    ctrl = _is_pressed("ctrl")
    win = _is_pressed(91) or _is_pressed(92)
    down = ctrl and win
    if down and not _recording:
        _recording = True
        start_recording()
    elif _recording and not down:
        _recording = False
        stop_recording()


def _foreground_title():
    """Title of the currently focused window (for focus-bound ESC / toggle)."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(512)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, 512)
        return buf.value or ""
    except Exception:
        return ""


def _toggle_paste_mode():
    """Shift+Tab: switch between CTRL+V and CTRL+SHIFT+V.

    Only effective while the dictation window is focused, so Shift+Tab stays
    untouched in every other app (editors, terminals, other tools).
    The key press is not suppressed (suppress=False), only observed.
    """
    global _paste_mode
    if "Local Dictation" not in _foreground_title():
        return
    _paste_mode = (_paste_mode + 1) % len(PASTE_MODES)
    print(f"  Paste mode: [{PASTE_MODES[_paste_mode].upper()}]        ")


threading.Thread(target=worker, daemon=True).start()
keyboard.hook(on_event)
keyboard.add_hotkey("shift+tab", _toggle_paste_mode, suppress=False)
# ESC quits ONLY when this dictation window is in the foreground.
# Otherwise an ESC in any other app would kill the tool globally.
while True:
    keyboard.wait("esc")
    if "Local Dictation" in _foreground_title():
        break
print("\nDone.")
