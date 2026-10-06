"""
config.py
----------
Centralized configuration for the Automotive Driver Monitoring System (DMS).
All thresholds, landmark indices, colors, and paths are defined here so that
no magic numbers appear elsewhere in the codebase.
"""

import os

import cv2

import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

WARNING_SOUND_PATH = os.path.join(ASSETS_DIR, "warning_beep.wav")
DROWSY_SOUND_PATH = os.path.join(ASSETS_DIR, "drowsy_alarm.wav")
LOG_FILE_PATH = os.path.join(LOGS_DIR, "fatigue_log.csv")

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
CAMERA_INDEX = 0
CAMERA_BACKEND_DSHOW = True  # Windows: cv2.CAP_DSHOW avoids empty-frame crashes
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# ---------------------------------------------------------------------------
# MediaPipe Face Mesh
# ---------------------------------------------------------------------------
MAX_NUM_FACES = 1
REFINE_LANDMARKS = True
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# ---------------------------------------------------------------------------
# Landmark indices (MediaPipe Face Mesh, refine_landmarks=True)
# ---------------------------------------------------------------------------
LEFT_EYE_IDX = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_IDX = [33, 160, 158, 133, 153, 144]
MOUTH_IDX = [61, 291, 39, 181, 0, 17, 269, 405]
POSE_LANDMARK_IDX = [1, 152, 33, 263, 61, 291]  # nose, chin, L-eye, R-eye, L-mouth, R-mouth

# Generic 3D face model (arbitrary units) used for solvePnP head pose estimation.
# No physical camera calibration is performed -- acceptable trade-off for a
# software-only prototype where sustained trend matters more than absolute
# angular accuracy.
MODEL_POINTS_3D = np.array([
    (0.0, 0.0, 0.0),           # Nose tip
    (0.0, -330.0, -65.0),      # Chin
    (-225.0, 170.0, -135.0),   # Left eye, left corner
    (225.0, 170.0, -135.0),    # Right eye, right corner
    (-150.0, -150.0, -125.0),  # Left mouth corner
    (150.0, -150.0, -125.0),   # Right mouth corner
], dtype=np.float64)

# ---------------------------------------------------------------------------
# Eye / Blink thresholds
# ---------------------------------------------------------------------------
EAR_THRESHOLD = 0.21           # below this => eye considered closed
BLINK_CONSEC_FRAMES = 2        # consecutive closed frames required to count a blink

# ---------------------------------------------------------------------------
# PERCLOS (Percentage of Eye Closure) -- primary drowsiness metric
# ---------------------------------------------------------------------------
PERCLOS_WINDOW_SECONDS = 10.0
PERCLOS_ALERT_THRESHOLD = 0.15    # mild sign -> ALERT
PERCLOS_WARNING_THRESHOLD = 0.40  # strong sign -> contributes to WARNING/DROWSY

# ---------------------------------------------------------------------------
# Mouth / Yawn thresholds
# ---------------------------------------------------------------------------
MAR_THRESHOLD = 0.6
YAWN_MIN_DURATION_SECONDS = 1.0
YAWN_WINDOW_SECONDS = 60.0
YAWN_COUNT_ALERT = 1
YAWN_COUNT_WARNING = 2

# ---------------------------------------------------------------------------
# Head pose thresholds
# ---------------------------------------------------------------------------
PITCH_DROOP_THRESHOLD_DEG = -15.0
PITCH_DROOP_MIN_DURATION_SECONDS = 2.0

# ---------------------------------------------------------------------------
# Face loss handling
# ---------------------------------------------------------------------------
FACE_LOST_WARNING_SECONDS = 2.0

# ---------------------------------------------------------------------------
# Alarm
# ---------------------------------------------------------------------------
SOUND_COOLDOWN_SECONDS = 3.0

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
FONT = cv2.FONT_HERSHEY_SIMPLEX

COLOR_PANEL = (40, 40, 40)
COLOR_TEXT_PRIMARY = (230, 230, 230)
COLOR_TEXT_SECONDARY = (160, 160, 160)

COLOR_NORMAL = (0, 200, 0)
COLOR_ALERT = (0, 210, 210)
COLOR_WARNING = (0, 165, 255)
COLOR_DROWSY = (0, 0, 255)

STATE_COLORS = {
    "NORMAL": COLOR_NORMAL,
    "ALERT": COLOR_ALERT,
    "WARNING": COLOR_WARNING,
    "DROWSY": COLOR_DROWSY,
}
