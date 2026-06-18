import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

import sys
import cv2
import time
import traceback

from eye_tracker      import EyeTracker
from blink_detector   import BlinkDetector
from mouse_controller import (MouseController, IS_WAYLAND, SCREEN_W, SCREEN_H,
                               _move, _root, check_compatibility, test_movement)
from config import CAMERA_ID, BLINK_THRESHOLD

WIN_W, WIN_H = 420, 280
WIN_X = SCREEN_W - WIN_W - 10
WIN_Y = SCREEN_H - WIN_H - 50


# ── Verified move: logs BEFORE + AFTER + SUCCESS/FAIL ─────
def _verified_move(x, y, label="gaze"):
    try:
        p_before = _root.query_pointer()
        print(f"[BEFORE] {label} cursor=({p_before.root_x},{p_before.root_y}) "
              f"-> target=({int(x)},{int(y)})")
        _move(x, y)
        p_after = _root.query_pointer()
        ok = abs(p_after.root_x - int(x)) < 8 and abs(p_after.root_y - int(y)) < 8
        print(f"[AFTER ] {'OK  ' if ok else 'FAIL'} "
              f"cursor=({p_after.root_x},{p_after.root_y})")
        return ok
    except Exception:
        print(f"[ERROR] _verified_move raised exception:")
        traceback.print_exc()
        return False


def draw_overlay(frame, data, ear_l, ear_r, event, cursor_pos):
    cv2.circle(frame, data["iris_left"],  7, (0,   255, 255), -1)
    cv2.circle(frame, data["iris_left"],  8, (0,   0,   0  ),  1)
    cv2.circle(frame, data["iris_right"], 7, (0,   255,   0), -1)
    cv2.circle(frame, data["iris_right"], 8, (0,   0,   0  ),  1)

    ls = "BLINK" if ear_l < BLINK_THRESHOLD else "open"
    rs = "BLINK" if ear_r < BLINK_THRESHOLD else "open"
    nx, ny = data["iris_norm"]
    cx, cy = cursor_pos

    lines = [
        (f"L:{ear_l:.2f}[{ls}] R:{ear_r:.2f}[{rs}]", (200, 255, 200)),
        (f"iris  ({nx:.3f},{ny:.3f})",                 (255, 255,   0)),
        (f"cursor({cx:4d},{cy:4d})",                   (0,   255, 128)),
    ]
    if event:
        lines.append((f"EVENT: {event}", (80, 80, 255)))

    for i, (txt, color) in enumerate(lines):
        cv2.putText(frame, txt, (8, 22 + i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, color, 1)

    cv2.putText(frame, "ESC=quit  M=test  T=jump(100,100)",
                (8, frame.shape[0] - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 120, 120), 1)


def run_move_test():
    print("[TEST] ── Manual move test ──────────────")
    for tx, ty, lbl in [(200, 200, "TOP-L"),
                        (SCREEN_W-200, 200, "TOP-R"),
                        (SCREEN_W//2, SCREEN_H//2, "CTR")]:
        _verified_move(tx, ty, lbl)
        time.sleep(0.4)
    print("[TEST] ── Done ──────────────────────────")


def main():
    if not check_compatibility():
        sys.exit(1)

    print("[TEST] Startup mouse movement test...")
    if not test_movement():
        print("[ERROR] Mouse movement failed. Run: python mouse_test.py")
        sys.exit(1)

    cam     = cv2.VideoCapture(CAMERA_ID)
    tracker = EyeTracker()
    blinker = BlinkDetector()
    mouse   = MouseController()

    cv2.namedWindow("Eye Mouse", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Eye Mouse", WIN_W, WIN_H)
    cv2.moveWindow("Eye Mouse", WIN_X, WIN_Y)

    print(f"[INFO] Backend  : {'WAYLAND+XWayland' if IS_WAYLAND else 'X11'} / Xlib")
    print(f"[INFO] Screen   : {SCREEN_W}x{SCREEN_H}")
    print(f"[INFO] Window   : {WIN_W}x{WIN_H} at bottom-right corner")
    print("[INFO] YELLOW=left iris (tracking)  GREEN=right iris")
    print("[INFO] Watch DESKTOP cursor — not inside webcam window!")
    print("[INFO] Keys: ESC=quit  M=move test  T=jump to (100,100)")

    # Verbose move logging for first 5 seconds
    verbose_until = time.time() + 5.0
    frame_n    = 0
    last_event = None
    event_exp  = 0.0
    cursor_pos = (0, 0)
    move_errors = 0

    while True:
        ok, frame = cam.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (WIN_W, WIN_H))

        try:
            data = tracker.process(frame)
        except Exception:
            print("[ERROR] tracker.process raised exception:")
            traceback.print_exc()
            data = None

        if time.time() > event_exp:
            last_event = None

        if data:
            ear_l = data["ear_left"]
            ear_r = data["ear_right"]
            nx, ny = data["iris_norm"]

            # ── Pipeline trace ─────────────────────────
            # Step 1: iris coords received
            # Step 2: call mouse.move — inside it calls _move(px,py)
            verbose = time.time() < verbose_until
            if verbose:
                print(f"[PIPE ] iris=({nx:.4f},{ny:.4f}) "
                      f"-> calling mouse.move()")

            try:
                mouse.move(nx, ny)
            except Exception:
                move_errors += 1
                print(f"[ERROR] mouse.move raised exception (#{move_errors}):")
                traceback.print_exc()

            # Step 3: read back actual cursor position
            try:
                p          = _root.query_pointer()
                cursor_pos = (p.root_x, p.root_y)
            except Exception:
                pass

            if verbose:
                print(f"[PIPE ] cursor now = {cursor_pos}")

            # Debug log every 60 frames
            if frame_n % 60 == 0:
                print(f"[DEBUG] f={frame_n:4d} | "
                      f"iris=({nx:.4f},{ny:.4f}) | "
                      f"cursor={cursor_pos} | "
                      f"EAR L={ear_l:.3f} R={ear_r:.3f}")

            # Blink → click (only after verbose phase)
            if time.time() > verbose_until:
                try:
                    event = blinker.update(ear_l, ear_r)
                    if event:
                        last_event = event
                        event_exp  = time.time() + 1.0
                        mouse.dispatch(event)
                except Exception:
                    print("[ERROR] blinker/dispatch exception:")
                    traceback.print_exc()

            draw_overlay(frame, data, ear_l, ear_r, last_event, cursor_pos)
        else:
            cv2.putText(frame, "No face detected",
                        (10, WIN_H // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow("Eye Mouse", frame)
        frame_n += 1

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        if key in (ord('m'), ord('M')):
            run_move_test()
        if key in (ord('t'), ord('T')):
            print("[T-KEY] Jumping cursor to (100,100)...")
            _verified_move(100, 100, "T-key")

    cam.release()
    cv2.destroyAllWindows()
    if move_errors:
        print(f"[WARN] {move_errors} move exceptions occurred during run.")
    print("[INFO] Stopped.")


if __name__ == "__main__":
    main()
