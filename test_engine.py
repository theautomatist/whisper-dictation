"""
Engine verification: loads faster-whisper large-v3 (int8) on the GPU and
transcribes an audio file. Measures load time, transcription time and the
real-time factor. Shows whether CUDA acceleration works.

Run:
    venv/Scripts/python.exe test_engine.py [audio.wav]
"""
import os
import sys
import time

# --- Make the CUDA DLLs from the pip packages nvidia-cublas/-cudnn discoverable ---
def _add_cuda_dlls():
    base = os.path.join(sys.prefix, "Lib", "site-packages", "nvidia")
    for sub in ("cublas", "cudnn"):
        p = os.path.join(base, sub, "bin")
        if os.path.isdir(p):
            os.add_dll_directory(p)

_add_cuda_dlls()

from faster_whisper import WhisperModel

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "jfk.wav")

_local = os.path.join(HERE, "models", "large-v3")
MODEL = _local if os.path.isfile(os.path.join(_local, "model.bin")) else "large-v3"
DEVICE = "cuda"
COMPUTE = "int8_float16"  # int8 weights, float16 activations -> fits in 6 GB

print(f"Loading model '{MODEL}' ({COMPUTE}) on {DEVICE} ...")
print("(On first run the model (~3 GB) is downloaded from HuggingFace.)")
t0 = time.time()
try:
    model = WhisperModel(MODEL, device=DEVICE, compute_type=COMPUTE)
    used = f"{DEVICE}/{COMPUTE}"
except Exception as e:
    print(f"\n[!] GPU init failed: {e}")
    print("    -> falling back to CPU (int8)")
    model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    used = "cpu/int8"
print(f"Model loaded in {time.time() - t0:.1f}s  ({used})\n")

print(f"Transcribing: {AUDIO}")
t1 = time.time()
segments, info = model.transcribe(AUDIO, beam_size=5)
text = " ".join(s.text.strip() for s in segments).strip()
dt = time.time() - t1

print("\n" + "=" * 60)
print(f"Detected language : {info.language} (p={info.language_probability:.2f})")
print(f"Audio length      : {info.duration:.1f}s")
print(f"Transcription time: {dt:.2f}s  ->  {info.duration / dt:.1f}x real-time")
print("=" * 60)
print(f"\nTEXT:\n{text}\n")
