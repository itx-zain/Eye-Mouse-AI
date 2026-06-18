# ─── Camera ───────────────────────────────────────────────
CAMERA_ID = 0

# ─── Cursor Smoothing ─────────────────────────────────────
SMOOTHING = 5

# ─── Blink Detection ──────────────────────────────────────
BLINK_THRESHOLD       = 0.21
BLINK_FRAMES          = 3
DOUBLE_BLINK_INTERVAL = 0.4
CLICK_COOLDOWN        = 0.6

# ─── Iris mapping (auto-updated by measure_iris.py) ───────
# These are calculated from live log data:
# Log shows when looking left:  iris_x ~ 0.35-0.38, iris_y ~ 0.62-0.64
# Log shows offset_x ~ -0.156, offset_y ~ +0.063
# Therefore: cx = iris_x - offset_x = 0.516, cy = iris_y - offset_y = 0.563
IRIS_CX = 0.51627
IRIS_CY = 0.56354

# Scale: use adaptive — computed every run from live iris range
# Set to 0 to trigger auto-compute on startup
IRIS_SCALE_X = 0
IRIS_SCALE_Y = 0
