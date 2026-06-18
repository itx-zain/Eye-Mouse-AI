"""
Standalone mouse backend diagnostic.
Run:  python mouse_test.py
"""
import os, time, subprocess
os.environ["QT_QPA_PLATFORM"] = "xcb"

print("=" * 55)
print("  MOUSE BACKEND DIAGNOSTIC")
print("=" * 55)
print(f"  XDG_SESSION_TYPE = {os.environ.get('XDG_SESSION_TYPE','NOT SET')}")
print(f"  DISPLAY          = {os.environ.get('DISPLAY','NOT SET')}")
print(f"  WAYLAND_DISPLAY  = {os.environ.get('WAYLAND_DISPLAY','NOT SET')}")
print(f"  XAUTHORITY       = {os.environ.get('XAUTHORITY','NOT SET')}")
print("=" * 55)

results = {}

# ── Backend 1: PyAutoGUI ──────────────────────────────────
print("\n[1] PyAutoGUI")
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE    = 0
    pyautogui.moveTo(200, 200)
    time.sleep(0.3)
    x, y = pyautogui.position()
    ok = abs(x - 200) < 5 and abs(y - 200) < 5
    print(f"    moveTo(200,200) -> ({x},{y}) -> {'SUCCESS' if ok else 'FAIL'}")
    results["pyautogui"] = ok
except Exception as e:
    print(f"    EXCEPTION: {e}")
    results["pyautogui"] = False

# ── Backend 2: Xlib warp_pointer ─────────────────────────
print("\n[2] Xlib warp_pointer")
try:
    from Xlib import display as xd
    d    = xd.Display()
    root = d.screen().root
    root.warp_pointer(500, 500); d.sync(); time.sleep(0.3)
    p  = root.query_pointer()
    ok = abs(p.root_x - 500) < 5 and abs(p.root_y - 500) < 5
    print(f"    warp(500,500) -> ({p.root_x},{p.root_y}) -> {'SUCCESS' if ok else 'FAIL'}")
    results["xlib"] = ok
except Exception as e:
    print(f"    EXCEPTION: {e}")
    results["xlib"] = False

# ── Backend 3: XTest fake_input ───────────────────────────
print("\n[3] XTest fake_input")
try:
    from Xlib import display as xd, X
    from Xlib.ext import xtest
    d    = xd.Display()
    root = d.screen().root
    xtest.fake_input(d, X.MotionNotify, False, X.CurrentTime, X.NONE, 300, 300)
    d.sync(); time.sleep(0.3)
    p  = root.query_pointer()
    ok = abs(p.root_x - 300) < 5 and abs(p.root_y - 300) < 5
    print(f"    fake_input(300,300) -> ({p.root_x},{p.root_y}) -> {'SUCCESS' if ok else 'FAIL'}")
    results["xtest"] = ok
except Exception as e:
    print(f"    EXCEPTION: {e}")
    results["xtest"] = False

# ── Backend 4: xdotool ────────────────────────────────────
print("\n[4] xdotool")
try:
    r = subprocess.run(
        ["xdotool", "mousemove", "400", "400"],
        capture_output=True, text=True
    )
    time.sleep(0.3)
    from Xlib import display as xd
    p  = xd.Display().screen().root.query_pointer()
    ok = abs(p.root_x - 400) < 5 and abs(p.root_y - 400) < 5
    print(f"    rc={r.returncode} stderr='{r.stderr.strip()}'")
    print(f"    xdotool(400,400) -> ({p.root_x},{p.root_y}) -> {'SUCCESS' if ok else 'FAIL'}")
    results["xdotool"] = ok
except Exception as e:
    print(f"    EXCEPTION: {e}")
    results["xdotool"] = False

# ── Summary ───────────────────────────────────────────────
print()
print("=" * 55)
print("  RESULTS SUMMARY")
print("=" * 55)
working = [k for k, v in results.items() if v]
failing = [k for k, v in results.items() if not v]
for k, v in results.items():
    print(f"  {'OK ' if v else 'FAIL'} {k}")

if working:
    print(f"\n  Best backend: {working[0]}")
    print("  Mouse movement IS working on this system.")
    print()
    print("  If cursor does not move in main.py:")
    print("  The OpenCV window may be capturing focus/cursor.")
    print("  Try moving your eyes and watch the desktop (not the cv2 window).")
else:
    print("\n  ALL backends FAILED.")
    print("  Possible reasons:")
    print("  1. Pure Wayland without XWayland")
    print("  2. Missing DISPLAY environment variable")
    print("  3. XAUTHORITY permission denied")
    print("  Fix: Log out → select 'Ubuntu on Xorg' → log back in")

print("=" * 55)
