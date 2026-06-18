import time
from config import BLINK_THRESHOLD, BLINK_FRAMES, DOUBLE_BLINK_INTERVAL, CLICK_COOLDOWN


class BlinkDetector:
    """
    Detects blink events from EAR values.

    Events returned:
      "left_click"   — left eye blink
      "right_click"  — right eye blink
      "double_click" — two left blinks within DOUBLE_BLINK_INTERVAL
    """

    def __init__(self):
        self._left_frames  = 0
        self._right_frames = 0

        self._last_left_blink  = 0.0   # timestamp of last left blink
        self._last_click_time  = 0.0   # cooldown tracker

    def update(self, ear_left, ear_right):
        """
        Call every frame. Returns an event string or None.
        """
        now = time.time()

        # Cooldown guard — ignore if too soon after last click
        if now - self._last_click_time < CLICK_COOLDOWN:
            # Still count frames so we don't miss the blink
            self._count_frames(ear_left, ear_right)
            return None

        event = self._detect(ear_left, ear_right, now)
        if event:
            self._last_click_time = now
        return event

    # ── private ──────────────────────────────────────────────

    def _count_frames(self, ear_left, ear_right):
        self._left_frames  = self._left_frames  + 1 if ear_left  < BLINK_THRESHOLD else 0
        self._right_frames = self._right_frames + 1 if ear_right < BLINK_THRESHOLD else 0

    def _detect(self, ear_left, ear_right, now):
        left_closed  = ear_left  < BLINK_THRESHOLD
        right_closed = ear_right < BLINK_THRESHOLD

        # Accumulate closed frames
        self._left_frames  = self._left_frames  + 1 if left_closed  else 0
        self._right_frames = self._right_frames + 1 if right_closed else 0

        # Left blink fired when eye just opened after enough closed frames
        if not left_closed and self._left_frames >= BLINK_FRAMES:
            self._left_frames = 0

            # Double blink?
            if now - self._last_left_blink <= DOUBLE_BLINK_INTERVAL:
                self._last_left_blink = 0.0   # reset so triple doesn't re-fire
                return "double_click"

            self._last_left_blink = now
            return "left_click"

        # Right blink
        if not right_closed and self._right_frames >= BLINK_FRAMES:
            self._right_frames = 0
            return "right_click"

        return None
