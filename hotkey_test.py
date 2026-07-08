"""
Hotkey diagnostics. Shows whether the keyboard hook works and under which
names CTRL and WINDOWS are detected.

Run:
    venv/Scripts/python.exe hotkey_test.py
"""
import keyboard

print("=== Part 1: which key names are valid? (without pressing anything) ===")
for name in ["ctrl", "left ctrl", "right ctrl", "windows", "left windows",
             "right windows", "win", "cmd", "super"]:
    try:
        r = keyboard.is_pressed(name)
        print(f"  is_pressed({name!r:16}) -> {r}   (name valid)")
    except Exception as ex:
        print(f"  is_pressed({name!r:16}) -> ERROR: {ex}")

print()
print("=== Part 2: live keys ===")
print("Now press CTRL + WINDOWS together (hold, then release).")
print("Every detected key is shown. ESC quits.\n")


def _is(name):
    try:
        return keyboard.is_pressed(name)
    except Exception:
        return False


def on_event(e):
    ctrl = _is("ctrl")
    win = _is("windows") or _is("left windows") or _is("right windows")
    combo = "  <<< CTRL+WIN DETECTED!" if (ctrl and win) else ""
    print(f"  {e.event_type:8} name={e.name!r:18} scan={e.scan_code}  "
          f"| ctrl={ctrl} win={win}{combo}", flush=True)


keyboard.hook(on_event)
keyboard.wait("esc")
print("\nDone.")
