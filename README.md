# Automotive Driver Monitoring System (DMS)

A real-time, software-only Driver Monitoring System prototype built with Python, OpenCV, and MediaPipe. It watches eye closure, yawning, and head pose to detect driver fatigue, raises visual and audio alerts, and logs every state change for later review — the same category of feature found in modern ADAS driver-monitoring stacks, implemented at prototype scale on a laptop webcam.

## Overview

The system captures live video, extracts 468 facial landmarks per frame via MediaPipe Face Mesh, derives three independent fatigue signals (Eye Aspect Ratio, Mouth Aspect Ratio, head pitch), and combines them in a time-aware state machine (`NORMAL → ALERT → WARNING → DROWSY`). State changes trigger visual overlays, audio alerts, and CSV logging.

## Architecture

```
                         main.py (owns camera loop, display)
                                     |
                    -------------------------------------
                    |                |                  |
           FaceMeshDetector   HeadPoseEstimator   camera_utils
        (detection/face_mesh)  (detection/head_pose)  (FPS, drawing)
                    |
        --------------------------
        |                        |
   eye_detection.py        yawn_detection.py
   (EAR, pure fn)           (MAR, pure fn)
        |                        |
        --------------------------
                    |
             fatigue_logic.py
      (PERCLOS, blink/yawn windows,
       droop duration, state machine)
                    |
          -----------------------
          |                     |
      logger.py              alarm.py
   (CSV, on transition)   (pygame, cooldown)
```

Detection modules are pure, reusable, and stateless (or self-contained where state is intrinsic, e.g. the MediaPipe model). All time-based reasoning — PERCLOS windows, yawn counting, sustained head droop, blink debouncing — lives in one place: `fatigue_logic.py`. `main.py` is the only file that touches the camera, the display window, or the keyboard.

## Folder Structure

```
Automotive_DMS/
├── main.py
├── config.py
├── fatigue_logic.py
├── logger.py
├── alarm.py
├── detection/
│   ├── face_mesh.py
│   ├── eye_detection.py
│   ├── yawn_detection.py
│   └── head_pose.py
├── utils/
│   └── camera_utils.py
├── assets/
│   ├── drowsy_alarm.wav
│   └── warning_beep.wav
├── logs/
│   └── fatigue_log.csv
├── requirements.txt
├── README.md
└── LICENSE
```

## Installation

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

## How to Run

```bash
python main.py
```

Press **`q`** to quit. A dashboard panel overlays live EAR/MAR/head-pose values, blink/yawn counts, PERCLOS, current driver state, FPS, and time. `logs/fatigue_log.csv` records every state transition.

## Core Concepts

### Eye Aspect Ratio (EAR)
A ratio of vertical eyelid distance to horizontal eye width, computed from six landmarks per eye. Open eyes produce a higher EAR (~0.25–0.35); closing eyes drive it toward ~0.1–0.15. A sustained low EAR over time (see PERCLOS below) is a stronger fatigue signal than any single frame.

### Mouth Aspect Ratio (MAR)
Same principle applied to the mouth: vertical lip opening relative to mouth width. Because a yawn is a sustained event (unlike a blink), yawns are confirmed by a minimum duration threshold rather than a single-frame check, avoiding false positives from talking or laughing.

### Head Pose Estimation (`solvePnP`)
A generic 3D face model is matched against six detected 2D landmarks using OpenCV's `solvePnP`, then converted to pitch/yaw/roll via Rodrigues rotation. No physical camera calibration is performed, so absolute angles are approximate — but the *trend* (sustained pitch dropping, i.e. head nodding forward) is reliable and is what the fatigue logic actually uses.

### PERCLOS (Percentage of Eye Closure)
The industry-standard drowsiness metric: the percentage of time within a rolling window (10 seconds here) that the eyes are classified as closed. PERCLOS is far more robust than instantaneous EAR because it filters out normal blinking and only flags sustained closure.

## Fatigue State Machine

| State | Trigger | Alert |
|---|---|---|
| `NORMAL` | No meaningful signals | None |
| `ALERT` | One mild indicator (PERCLOS ≥ 0.15, or 1 yawn in 60s) | Visual only |
| `WARNING` | One strong signal (PERCLOS ≥ 0.40, 2+ yawns in 60s, or sustained head droop ≥ 2s) | Orange border + beep |
| `DROWSY` | Two or more strong signals simultaneously | Red border + alarm |

All thresholds live in `config.py` — no magic numbers elsewhere in the codebase.

## Future Improvements

- Proper camera calibration (checkerboard method) for accurate absolute head-pose angles
- Per-driver EAR/MAR baseline calibration at session start (accounts for natural eye-shape variation)
- Embedded deployment on an automotive-grade SoC (e.g. Qualcomm Snapdragon Ride, NVIDIA Jetson) with hardware-accelerated inference
- Integration with a vehicle's CAN bus to trigger real dashboard/cluster alerts instead of a software overlay
- Dedicated camera module evaluation: an OpenMV camera was tested for USB-serial video transport during development; measured frame rate (~1–3 FPS over USB VCP) was insufficient for real-time fatigue detection, so the laptop webcam was used instead. A higher-bandwidth interface (e.g. MIPI-CSI to an embedded SoC) would be required for a genuinely embedded version of this pipeline.

## Interview Explanation

If asked to walk through this project: start with the signal layer (EAR/MAR/head pose are independent, well-understood computer-vision metrics), then explain why no single signal is trusted alone — PERCLOS smooths out normal blinking, yawn detection uses duration instead of instantaneous state, and head droop requires sustained deviation, not a single noisy frame. The state machine requiring two simultaneous strong signals for `DROWSY` is a deliberate false-positive reduction strategy. The architecture itself (detection modules as pure functions, state machine centralized in one file, camera/display isolated to `main.py`) demonstrates separation of concerns, which is exactly what a reviewer at an automotive software team is checking for beyond "does the demo work."

## Screenshots

*(Add screenshots of the running dashboard here — `NORMAL`, `WARNING`, and `DROWSY` states recommended.)*
