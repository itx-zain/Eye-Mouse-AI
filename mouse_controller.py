import os
import subprocess
import time
import math
from collections import deque
from config import SMOOTHING

SESSION     = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
IS_WAYLAND  = "wayland" in SESSION
HAS_DISPLAY = bool(os.environ.get("DISPLAY", ""))


def _screen_size():
    try:
        out = subprocess.check_output(
            ["xrandr", "--current"], stderr=subprocess.DEVNULL).decode()
        for line in out.splitlines():
            if " connected" in line:
                for part in line.split():
                    if "x" in part and "+" in part:
                        w, h = part.split("+")[0].split("x")
                        return int(w), int(h)
    except Exception:
        pass
    return 1366, 768


SCREEN_W, SCREEN_H = _screen_size()


# ── Backend detection ──────────────────────────────────────
def _try_uinput():
    """
    Real Wayland cursor via /dev/uinput.
    Works on GNOME Wayland — bypasses XWayland virtual pointer.
    Requires: sudo usermod -aG input $USER  (then relogin)
              OR: sudo chmod 666 /dev/uinput  (temporary)
    """
    try:
        from evdev import UInput, ecodes as e, AbsInfo
        cap = {
            e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
            e.EV_ABS: [
                (e.ABS_X, AbsInfo(value=0, min=0, max=SCREEN_W-1,
                                  fuzz=0, flat=0, resolution=1)),
                (e.ABS_Y, AbsInfo(value=0, min=0, max=SCREEN_H-1,
                                  fuzz=0, flat=0, resolution=1)),
            ],
        }
        ui = UInput(cap, name="eye-mouse", version=0x3,
                    input_props=[0x40])  # INPUT_PROP_POINTER
        time.sleep(0.1)
        return ui, e
    except Exception as err:
        return None, err


def _try_xlib():
    try:
        from Xlib import display as xd, X
        from Xlib.ext import xtest
        d    = xd.Display()
        root = d.screen().root
        return d, root, X, xtest
    except Exception:
        return None, None, None, None


def check_compatibility():
    print("=" * 55)
    print(f"  Session : {SESSION.upper()} | Screen: {SCREEN_W}x{SCREEN_H}")
    print(f"  DISPLAY : {os.environ.get('DISPLAY','none')} | "
          f"WAYLAND: {os.environ.get('WAYLAND_DISPLAY','none')}")
    print("=" * 55)

    if IS_WAYLAND:
        print("[INFO] Wayland session detected.")
        print("[INFO] Testing backends...")

        # Try uinput first (real Wayland cursor)
        ui, e = _try_uinput()
        if ui is not None:
            ui.close()
            print("[INFO] uinput: AVAILABLE — real Wayland cursor ✓")
            return True

        print(f"[WARN] uinput: NOT available ({e})")
        print("[WARN] Falling back to Xlib (XWayland virtual pointer).")
        print("[WARN] Cursor may not be visible on Wayland desktop.")
        print()
        print("  To fix — run ONCE in terminal:")
        print("  bash setup_wayland.sh")
        print("  Then: newgrp input && python main.py")
        print()

        if not HAS_DISPLAY:
            print("[ERROR] No DISPLAY — cannot even use Xlib fallback.")
            return False

    d, root, X, xtest = _try_xlib()
    if d:
        backend = "Xlib/XWayland (virtual)" if IS_WAYLAND else "Xlib/X11"
        print(f"[INFO] {backend}: AVAILABLE")
        return True

    print("[ERROR] No working mouse backend found.")
    return False


def test_movement():
    print("[TEST] Mouse movement test...")
    d, root, X, xtest = _try_xlib()
    if not d:
        print("[TEST] FAIL — Xlib not available")
        return False
    for tx, ty in [(200, 200), (SCREEN_W-200, 200), (SCREEN_W//2, SCREEN_H//2)]:
        root.warp_pointer(tx, ty); d.sync(); time.sleep(0.2)
        p = root.query_pointer()
        ok = abs(p.root_x-tx) < 5 and abs(p.root_y-ty) < 5
        status = "OK" if ok else "FAIL"
        print(f"  ({tx},{ty}) -> ({p.root_x},{p.root_y}) [{status}]")
        if not ok:
            return False
    print("[TEST] OK\n")
    return True


# ── Initialise best available backend ────────────────────
_uinput_dev  = None
_uinput_e    = None
_xlib_d      = None
_xlib_root   = None
_xlib_xtest  = None
_xlib_X      = None
_backend     = "none"

# Try uinput first
_ui, _e = _try_uinput()
if _ui is not None:
    _uinput_dev = _ui
    _uinput_e   = _e
    _backend    = "uinput"
    print(f"[MOUSE] Backend: uinput (real Wayland pointer)")
else:
    # Fall back to Xlib
    _xlib_d, _xlib_root, _xlib_X, _xlib_xtest = _try_xlib()
    if _xlib_d:
        _backend = "xlib"
        label = "Xlib/XWayland (virtual pointer)" if IS_WAYLAND else "Xlib/X11"
        print(f"[MOUSE] Backend: {label}")
        if IS_WAYLAND:
            print("[MOUSE] WARNING: cursor moves are virtual on Wayland!")
            print("[MOUSE] Run 'bash setup_wayland.sh' for real cursor.")
    else:
        print("[MOUSE] ERROR: no backend available")

print(f"[MOUSE] Screen : {SCREEN_W}x{SCREEN_H}")

# Expose _root for main.py to query cursor position
if _xlib_root:
    _root = _xlib_root
else:
    # Dummy root that always returns 0,0
    class _FakeRoot:
        class _Ptr:
            root_x = 0; root_y = 0
        def query_pointer(self): return self._Ptr()
    _root = _FakeRoot()


def _move(x, y):
    x, y = int(x), int(y)
    if _backend == "uinput":
        e = _uinput_e
        _uinput_dev.write(e.EV_ABS, e.ABS_X, x)
        _uinput_dev.write(e.EV_ABS, e.ABS_Y, y)
        _uinput_dev.syn()
        print(f"[DEBUG] uinput move to ({x},{y})")
    elif _backend == "xlib":
        _xlib_root.warp_pointer(x, y)
        _xlib_d.sync()
        print(f"[DEBUG] xlib move to ({x},{y})")
    else:
        print(f"[WARN] _move called but backend is '{_backend}'")


def _click_btn(btn, press):
    if _backend == "uinput":
        e = _uinput_e
        _uinput_dev.write(
            e.EV_KEY, btn,
            1 if press else 0
        )
        _uinput_dev.syn()
    elif _backend == "xlib":
        from Xlib import X
        t = X.ButtonPress if press else X.ButtonRelease
        _xlib_xtest.fake_input(_xlib_d, t, btn)
        _xlib_d.sync()


def _click_left():
    e = _uinput_e
    if _backend == "uinput":
        _click_btn(e.BTN_LEFT, True);  _click_btn(e.BTN_LEFT, False)
    elif _backend == "xlib":
        _click_btn(1, True);  _click_btn(1, False)


def _click_right():
    e = _uinput_e
    if _backend == "uinput":
        _click_btn(e.BTN_RIGHT, True);  _click_btn(e.BTN_RIGHT, False)
    elif _backend == "xlib":
        _click_btn(3, True);  _click_btn(3, False)


def _double_click():
    _click_left(); time.sleep(0.05); _click_left()


# ── One-Euro filter ────────────────────────────────────────
class _OneEuro:
    def __init__(self, freq=30, min_cutoff=1.5, beta=0.8):
        self.freq=freq; self.mco=min_cutoff; self.beta=beta
        self.xp=None; self.dxp=0.0

    def _a(self, co):
        return 1.0/(1.0+1.0/(2*math.pi*co*(1.0/self.freq)))

    def __call__(self, x):
        if self.xp is None: self.xp=x; return x
        dx  = (x-self.xp)*self.freq
        dxh = self._a(1.0)*dx+(1-self._a(1.0))*self.dxp
        a   = self._a(self.mco+self.beta*abs(dxh))
        xh  = a*x+(1-a)*self.xp
        self.xp=xh; self.dxp=dxh; return xh


# ── Iris range (measured: lm[468] on typical webcam) ──────
IRIS_X_MIN = 0.429 - 0.154 * 1.5
IRIS_X_MAX = 0.429 + 0.154 * 1.5
IRIS_Y_MIN = 0.649 - 0.107 * 1.5
IRIS_Y_MAX = 0.649 + 0.107 * 1.5

print(f"[MOUSE] Iris X : [{IRIS_X_MIN:.3f} – {IRIS_X_MAX:.3f}]")
print(f"[MOUSE] Iris Y : [{IRIS_Y_MIN:.3f} – {IRIS_Y_MAX:.3f}]")


class MouseController:
    def __init__(self):
        self._fx    = _OneEuro()
        self._fy    = _OneEuro()
        self._log_t = 0.0
        self._x_min = IRIS_X_MIN
        self._x_max = IRIS_X_MAX
        self._y_min = IRIS_Y_MIN
        self._y_max = IRIS_Y_MAX

    def move(self, norm_x, norm_y):
        # Expand range as eyes move
        self._x_min = min(self._x_min, norm_x)
        self._x_max = max(self._x_max, norm_x)
        self._y_min = min(self._y_min, norm_y)
        self._y_max = max(self._y_max, norm_y)

        span_x = max(self._x_max - self._x_min, 0.05)
        span_y = max(self._y_max - self._y_min, 0.02)

        rx = max(0.0, min(1.0, (norm_x - self._x_min) / span_x))
        ry = max(0.0, min(1.0, (norm_y - self._y_min) / span_y))

        px = max(0.0, min(SCREEN_W-1.0, self._fx(rx * SCREEN_W)))
        py = max(0.0, min(SCREEN_H-1.0, self._fy(ry * SCREEN_H)))

        _move(px, py)

        now = time.time()
        if now - self._log_t > 1.0:
            print(f"[MOVE] iris=({norm_x:.4f},{norm_y:.4f})  "
                  f"screen=({int(px)},{int(py)})  backend={_backend}")
            self._log_t = now

    def dispatch(self, event):
        print(f"[CLICK] {event}")
        if event == "left_click":     _click_left()
        elif event == "right_click":  _click_right()
        elif event == "double_click": _double_click()
