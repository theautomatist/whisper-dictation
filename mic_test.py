"""
Microphone test: records a few seconds and shows the input level.
This is how you find out which mic actually delivers signal.

Run:
    venv/Scripts/python.exe mic_test.py            # default microphone
    venv/Scripts/python.exe mic_test.py 19         # specific device (index from the list)
    venv/Scripts/python.exe mic_test.py list       # only show the device list
"""
import sys
import time
import numpy as np
import sounddevice as sd

if len(sys.argv) > 1 and sys.argv[1] == "list":
    print(sd.query_devices())
    print("\nDefault [input, output]:", sd.default.device)
    sys.exit(0)

device = int(sys.argv[1]) if len(sys.argv) > 1 else None
dur = 6
sr = 16000

name = sd.query_devices(device if device is not None else sd.default.device[0])["name"]
print(f"Testing microphone: {name}")
print(f"Recording {dur} seconds -> PLEASE SPEAK LOUDLY NOW ...\n")

rec = sd.rec(int(dur * sr), samplerate=sr, channels=1, dtype="float32", device=device)
for s in range(dur):
    time.sleep(1)
    chunk = rec[: int((s + 1) * sr)]
    peak = float(np.abs(chunk).max()) if len(chunk) else 0.0
    bar = "#" * int(peak * 60)
    print(f"  {s+1}s  level {peak:0.3f}  |{bar}")
sd.wait()

peak = float(np.abs(rec).max())
rms = float(np.sqrt((rec ** 2).mean()))
print(f"\nResult: peak level={peak:.3f}  average(RMS)={rms:.4f}")
if peak < 0.01:
    print(">>> NO SIGNAL. Wrong mic, muted, or level at 0.")
    print(">>> Tip: 'mic_test.py list' shows all devices; try a different index.")
elif peak < 0.05:
    print(">>> VERY QUIET. Turn up the mic level in Windows.")
else:
    print(">>> Signal OK! This device works. Remember the index.")
