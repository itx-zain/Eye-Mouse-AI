"""
Run this script to re-measure your iris center and scale.
It updates config.py automatically.
Usage: python measure_iris.py
"""
import cv2, mediapipe as mp, time, os, re
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

os.environ["QT_QPA_PLATFORM"] = "xcb"

MODEL_PATH = "face_landmarker.task"
lm_model = vision.FaceLandmarker.create_from_options(
    vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
        num_faces=1))

cam = cv2.VideoCapture(0)

# Phase 1: center
print("Phase 1/2 — Look straight at screen center for 5 seconds...")
xs, ys = [], []
start = time.time()
while time.time() - start < 5:
    ok, frame = cam.read()
    if not ok: continue
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    r = lm_model.detect(img)
    if r.face_landmarks:
        lm = r.face_landmarks[0]
        xs.append(lm[473].x)
        ys.append(lm[473].y)
    time.sleep(0.033)

xs.sort(); ys.sort()
mid = len(xs) // 2
cx = xs[mid]; cy = ys[mid]
print(f"  Center: cx={cx:.5f}  cy={cy:.5f}")

# Phase 2: span
print("\nPhase 2/2 — Move eyes to ALL corners slowly for 8 seconds...")
xs2, ys2 = [], []
start = time.time()
while time.time() - start < 8:
    ok, frame = cam.read()
    if not ok: continue
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    r = lm_model.detect(img)
    if r.face_landmarks:
        lm = r.face_landmarks[0]
        xs2.append(lm[473].x)
        ys2.append(lm[473].y)
    time.sleep(0.033)

cam.release()

span_x = max(xs2) - min(xs2)
span_y = max(ys2) - min(ys2)
span_x = max(span_x, 0.02)
span_y = max(span_y, 0.01)

from Xlib import display as xd
d = xd.Display(); s = d.screen()
sw, sh = s.width_in_pixels, s.height_in_pixels

scale_x = sw / span_x
scale_y = sh / span_y

print(f"  Span: ({span_x:.5f}, {span_y:.5f})")
print(f"  Scale: ({scale_x:.0f}, {scale_y:.0f})")

# Update config.py
with open("config.py", "r") as f:
    content = f.read()

content = re.sub(r"IRIS_CX\s*=.*",    f"IRIS_CX = {cx:.5f}",      content)
content = re.sub(r"IRIS_CY\s*=.*",    f"IRIS_CY = {cy:.5f}",      content)
content = re.sub(r"IRIS_SCALE_X\s*=.*", f"IRIS_SCALE_X = {scale_x:.0f}", content)
content = re.sub(r"IRIS_SCALE_Y\s*=.*", f"IRIS_SCALE_Y = {scale_y:.0f}", content)

with open("config.py", "w") as f:
    f.write(content)

print("\nconfig.py updated!")
print(f"  IRIS_CX={cx:.5f}  IRIS_CY={cy:.5f}")
print(f"  IRIS_SCALE_X={scale_x:.0f}  IRIS_SCALE_Y={scale_y:.0f}")
print("\nNow run: python main.py")
