import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import urllib.request
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "face_landmarker.task")
MODEL_URL  = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

# ── Iris indices ──────────────────────────────────────────
# lm[468] = left  iris center
# lm[473] = right iris center
LEFT_IRIS_IDX  = 468
RIGHT_IRIS_IDX = 473

# EAR indices
LEFT_EYE_EAR  = [386, 374, 385, 380, 362, 263]
RIGHT_EYE_EAR = [159, 145, 160, 144,  33, 133]


def _download_model():
    if not os.path.exists(MODEL_PATH):
        print("[INFO] Downloading face_landmarker.task (~30 MB)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("[INFO] Download done.")


def _ear(lm, indices, w, h):
    pts = [np.array([lm[i].x * w, lm[i].y * h]) for i in indices]
    A = np.linalg.norm(pts[0] - pts[1])
    B = np.linalg.norm(pts[2] - pts[3])
    C = np.linalg.norm(pts[4] - pts[5])
    return (A + B) / (2.0 * C)


class EyeTracker:
    def __init__(self):
        _download_model()
        opts = vision.FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
            num_faces=1,
            min_face_detection_confidence=0.6,
            min_face_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        self._lm = vision.FaceLandmarker.create_from_options(opts)

    def process(self, frame):
        h, w = frame.shape[:2]
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self._lm.detect(
            mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

        if not result.face_landmarks:
            return None

        lm = result.face_landmarks[0]

        def px(idx):
            return int(lm[idx].x * w), int(lm[idx].y * h)

        # Use left iris (468) for mouse — moves most clearly with gaze
        # Return normalized coordinates for the tracking iris (left iris)
        return {
            "iris_left":       px(LEFT_IRIS_IDX),
            "iris_right":      px(RIGHT_IRIS_IDX),
            "ear_left":        _ear(lm, LEFT_EYE_EAR,  w, h),
            "ear_right":       _ear(lm, RIGHT_EYE_EAR, w, h),
            "iris_norm":       (lm[LEFT_IRIS_IDX].x, lm[LEFT_IRIS_IDX].y),
        }
