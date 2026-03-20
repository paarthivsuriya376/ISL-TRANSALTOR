"""
utils/hand_tracking.py  (v3 – motion-aware)

Uses ONLY mp.solutions.hands.
Adds a wrist-position buffer so we can detect:
  - GOODBYE  → open palm + fast lateral motion
  - NO       → index finger + fast lateral wag
  - YES      → fist/thumb + fast vertical motion
"""

import cv2, math, mediapipe as mp
from collections import deque

MOTION_HISTORY = 10   # frames to keep


class HandSignDetector:
    TIPS = [4, 8, 12, 16, 20]

    def __init__(self):
        self._mp_hands = mp.solutions.hands
        self._hands    = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6,
        )
        self._mp_draw  = mp.solutions.drawing_utils
        self._mp_style = mp.solutions.drawing_styles
        self._results  = None
        # Motion buffer: deque of (wx, wy) per hand
        self._motion   = {0: deque(maxlen=MOTION_HISTORY),
                          1: deque(maxlen=MOTION_HISTORY)}

    # ------------------------------------------------------------------ #
    def find_hands(self, frame_bgr, draw=True):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self._results = self._hands.process(rgb)
        if draw and self._results.multi_hand_landmarks:
            for lm in self._results.multi_hand_landmarks:
                self._mp_draw.draw_landmarks(
                    frame_bgr, lm,
                    self._mp_hands.HAND_CONNECTIONS,
                    self._mp_style.get_default_hand_landmarks_style(),
                    self._mp_style.get_default_hand_connections_style(),
                )
        return frame_bgr

    def num_hands(self):
        if self._results and self._results.multi_hand_landmarks:
            return len(self._results.multi_hand_landmarks)
        return 0

    def recognize_both_hands(self, frame_bgr):
        if not self._results or not self._results.multi_hand_landmarks:
            return None

        h, w, _ = frame_bgr.shape
        labels  = []

        for i, hand_lm in enumerate(self._results.multi_hand_landmarks):
            lm = [[id, int(p.x * w), int(p.y * h)]
                  for id, p in enumerate(hand_lm.landmark)]
            # Update motion buffer
            if i in self._motion:
                self._motion[i].append((lm[0][1], lm[0][2]))
            
            label = self._classify(lm, i)
            if label:
                labels.append(label)

        if not labels:
            return None
        
        # Sort labels to ensure stable comparison (e.g. ['S', 'S'] or ['A', 'B'])
        return sorted(labels)

    # Legacy stubs
    def get_position(self, img, hand_no=0): return []
    def recognize_sign(self, lm, hand_no=0): return None

    # ------------------------------------------------------------------ #
    # Finger states
    # ------------------------------------------------------------------ #
    def _fingers_open(self, lm):
        open_list = []
        # Thumb: tip further from wrist than IP
        d_tip = self._dist(lm[4], lm[0])
        d_ip  = self._dist(lm[3], lm[0])
        open_list.append(d_tip > d_ip)
        # Fingers: tip y above pip y
        for tip in self.TIPS[1:]:
            open_list.append(lm[tip][2] < lm[tip - 2][2])
        return open_list

    @staticmethod
    def _dist(a, b):
        return math.hypot(a[1] - b[1], a[2] - b[2])

    # ------------------------------------------------------------------ #
    # Motion helpers
    # ------------------------------------------------------------------ #
    def _motion_vec(self, hand_no):
        """Returns (dx, dy) over history, or (0,0) if not enough data."""
        buf = self._motion[hand_no]
        if len(buf) < 4:
            return 0, 0
        dx = buf[-1][0] - buf[0][0]
        dy = buf[-1][1] - buf[0][1]
        return dx, dy

    def _is_waving(self, hand_no, threshold=25):
        """True if the hand is moving significantly left/right."""
        dx, dy = self._motion_vec(hand_no)
        return abs(dx) > threshold

    def _is_nodding(self, hand_no, threshold=20):
        """True if the hand is moving significantly up/down."""
        dx, dy = self._motion_vec(hand_no)
        return abs(dy) > threshold

    # ------------------------------------------------------------------ #
    # Main classifier
    # ------------------------------------------------------------------ #
    def _classify(self, lm, hand_no):
        th, ix, mi, ri, pk = self._fingers_open(lm)
        n = sum([th, ix, mi, ri, pk])

        waving  = self._is_waving(hand_no, 22)
        nodding = self._is_nodding(hand_no, 18)
        dx, dy  = self._motion_vec(hand_no)
        moving_up   = dy < -18
        moving_down = dy > 18

        # ----------------------------------------------------------------
        # ★ Motion-dependent gestures (checked FIRST)
        # ----------------------------------------------------------------

        # GOODBYE: open palm moving sideways
        if n == 5 and waving:
            return "GOODBYE 👋"

        # NO: index or index+middle wagging side to side
        if not th and ix and not ri and not pk and waving:
            return "NO 🚫"
        if not th and ix and mi and not ri and not pk and waving:
            return "NO 🚫"

        # YES: fist (or thumb up) nodding up/down
        if n == 0 and nodding:
            return "YES ✅"
        if th and not ix and not mi and not ri and not pk and nodding:
            return "YES ✅"

        # COME: beckoning – open palm moving towards body (upward in mirrored)
        if n >= 4 and moving_up and not waving:
            return "COME HERE"

        # GO AWAY: open palm pushing away (downward / forward)
        if n >= 4 and moving_down and not waving:
            return "GO AWAY"

        # SORRY: fist circular motion (waving + nodding together)
        if n == 0 and waving and nodding:
            return "SORRY"

        # ----------------------------------------------------------------
        # ★ Static gestures
        # ----------------------------------------------------------------

        # All 5 open (static) → HELLO / STOP
        if n == 5:
            return "HELLO / STOP ✋"

        # All closed (static fist)
        if n == 0:
            return "S"

        # Thumb only
        if th and not ix and not mi and not ri and not pk:
            if lm[4][2] < lm[0][2]:
                return "GOOD 👍"
            else:
                return "BAD 👎"

        # ILY: thumb + index + pinky
        if th and ix and not mi and not ri and pk:
            return "I LOVE YOU 🤟"

        # Index only
        if not th and ix and not mi and not ri and not pk:
            return "YES / ATTENTION ☝️"

        # Pinky only
        if not th and not ix and not mi and not ri and pk:
            return "I"

        # Index + Middle (V)
        if not th and ix and mi and not ri and not pk:
            return "PEACE ✌️"

        # Thumb + Index (L)
        if th and ix and not mi and not ri and not pk:
            return "L"

        # Thumb + Middle + Pinky
        if th and not ix and mi and not ri and pk:
            return "SPIDER-MAN 🕷️"

        # Index + Pinky
        if not th and ix and not mi and not ri and pk:
            return "CALL ME 🤙"

        # Three fingers (index + middle + ring)
        if not th and ix and mi and ri and not pk:
            return "W"

        # Four fingers up (no thumb)
        if not th and ix and mi and ri and pk:
            return "HELP / B 🤚"

        # Thumb + Index + Middle
        if th and ix and mi and not ri and not pk:
            return "K"

        return None
