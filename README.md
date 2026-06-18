# Eye Mouse — AI Gaze-Controlled Mouse

Control your computer mouse using only your eyes. No hands needed.

Built with Python, OpenCV, MediaPipe Face Mesh, and Xlib.

---

## Features

| Feature | Detail |
|---|---|
| Gaze tracking | Real-time iris detection using MediaPipe Face Mesh |
| Mouse movement | Cursor follows your eye gaze across the full screen |
| Left blink | Left click |
| Right blink | Right click |
| Double blink | Double click |
| Both eyes tracked | Yellow dot = left iris, Green dot = right iris |
| Smooth movement | One-Euro filter removes jitter |
| Adaptive range | Auto-adjusts to your eye movement range |
| Wayland support | Works on Wayland via XWayland + Xlib |
| X11 support | Full native support |

---

## Project Structure

```
ai mouse decator/
├── main.py              — Main application loop
├── eye_tracker.py       — Face mesh + iris landmark detection
├── blink_detector.py    — EAR-based blink → click events
├── mouse_controller.py  — Xlib mouse backend + adaptive mapping
├── config.py            — All tunable settings
├── mouse_test.py        — Standalone mouse backend diagnostic
├── measure_iris.py      — Re-measure your iris center/range
├── requirements.txt     — Python dependencies
└── face_landmarker.task — MediaPipe model (auto-downloaded)
```

---

## Requirements

- Python 3.10+
- Webcam
- Linux (Ubuntu 22.04+ tested)
- X11 or Wayland with XWayland

---

## Installation

**1. Clone the project**

```bash
git clone <your-repo-url>
cd "ai mouse decator"
```

**2. Create virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
pip install python-xlib
```

**4. Linux system packages**

```bash
sudo apt install python3-tk xdotool
```

---

## Run

```bash
python main.py
```

On first run, the MediaPipe model (`face_landmarker.task`, ~30 MB) downloads automatically.

---

## Usage

### Startup

The app runs a mouse movement test before starting. If it fails, run the diagnostic:

```bash
python mouse_test.py
```

### Controls

| Key | Action |
|---|---|
| `ESC` | Quit |
| `M` | Manual mouse test — moves cursor to 3 positions |

### Eye Controls

| Action | Result |
|---|---|
| Look left/right/up/down | Mouse cursor moves |
| Left eye blink | Left click |
| Right eye blink | Right click |
| Double blink (left eye) | Double click |

### Camera Window

The webcam window is small (`420×280`) and pinned to the **bottom-right corner** of your screen so the desktop is always visible.

- **Yellow dot** — left iris (used for tracking)
- **Green dot** — right iris

---

## Configuration

Edit `config.py` to tune the app:

```python
CAMERA_ID   = 0       # change if you have multiple cameras

SMOOTHING   = 5       # cursor smoothing strength

# Blink detection
BLINK_THRESHOLD       = 0.21   # EAR below this = eye closed
BLINK_FRAMES          = 3      # frames eye must stay closed
DOUBLE_BLINK_INTERVAL = 0.4    # seconds between 2 blinks = double click
CLICK_COOLDOWN        = 0.6    # cooldown after each click
```

---

## Wayland vs X11

This app runs on both. On **Wayland**, it uses **XWayland + Xlib** automatically.

### How to check your session

```bash
echo $XDG_SESSION_TYPE
```

### If cursor does not move on Wayland

Make sure XWayland is running:

```bash
echo $DISPLAY   # should print :0
```

If `DISPLAY` is empty, switch to X11:

1. Log out
2. On the login screen, click the **gear icon ⚙**
3. Select **Ubuntu on Xorg** (or GNOME on Xorg)
4. Log in and re-run

---

## Recent Fixes

### Bug Fix: Cursor Not Moving
**Issue**: The cursor was not moving on the screen when using eye tracking.

**Root Cause**: In `eye_tracker.py`, the normalized iris coordinates key was incorrectly named `iris_right_norm` but was actually using the left iris index (`LEFT_IRIS_IDX = 468`). This caused confusion and potential key errors.

**Fix Applied**:
- Renamed `iris_right_norm` to `iris_norm` in `eye_tracker.py`
- Updated `main.py` to use the correct key name
- Added debug logging to `mouse_controller.py` to track movement commands

**Verification**: Run `python test_cursor_fix.py` to verify the fixes are working.

---

## Troubleshooting

### Mouse does not move

Run the diagnostic:

```bash
python mouse_test.py
```

This tests all 4 backends (PyAutoGUI, Xlib, XTest, xdotool) and prints `SUCCESS` or `FAILURE` for each.

### Cursor stays in one corner

Your iris range may be off. Re-measure:

```bash
python measure_iris.py
```

Follow the on-screen prompts — look straight at the screen for 5 seconds, then move your eyes to all corners for 8 seconds. Values are saved to `config.py` automatically.

### Blink not detected

Increase sensitivity in `config.py`:

```python
BLINK_THRESHOLD = 0.25   # raise this value
```

### Camera not found

```python
CAMERA_ID = 1   # try 1 or 2 in config.py
```

### MediaPipe warnings on startup

These are harmless GPU/EGL init messages — the app works normally.

---

## How It Works

```
Webcam frame
    │
    ▼
EyeTracker (MediaPipe Face Mesh)
    │  478 face landmarks
    │  lm[468] = left iris center
    │  lm[473] = right iris center
    │  EAR = Eye Aspect Ratio per eye
    ▼
BlinkDetector
    │  EAR < threshold for N frames = blink
    │  Left blink  → left click
    │  Right blink → right click
    │  2× left blink → double click
    ▼
MouseController
    │  Iris (0–1) → screen coords via adaptive range mapping
    │  One-Euro filter removes jitter
    │  Xlib warp_pointer moves OS cursor
    ▼
Desktop cursor moves
```

### Iris to Screen Mapping

Iris coordinates are normalised `0.0–1.0`. The app tracks the observed min/max range of your iris movement and maps it to full screen width/height. The range expands automatically as you move your eyes — no calibration step needed.

### One-Euro Filter

Removes high-frequency jitter while keeping fast movements responsive. Faster eye movement = less smoothing. Slow drift = heavily smoothed.

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| opencv-python | ≥ 4.8.0 | Webcam capture and display |
| mediapipe | ≥ 0.10.0 | Face mesh and iris landmarks |
| numpy | ≥ 1.24.0 | EAR geometry calculations |
| python-xlib | latest | Mouse movement via Xlib |
| pyautogui | ≥ 0.9.54 | Fallback mouse backend |
| pynput | ≥ 1.7.6 | Fallback mouse backend |

---

## License

MIT License — free to use, modify, and distribute.
