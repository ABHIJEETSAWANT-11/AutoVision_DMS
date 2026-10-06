"""
main.py
---------
Entry point for the Automotive Driver Monitoring System (DMS).

Orchestrates: camera capture -> face mesh detection -> EAR/MAR/head-pose
signal extraction -> fatigue state machine -> alerts + logging ->
dashboard display.

This is the ONLY file in the project that owns cv2.VideoCapture, the
main loop, cv2.imshow, and cv2.waitKey. Every other module is a pure,
reusable processing component with no camera or display responsibility.

Run with:
    python main.py
Press 'q' to quit.
"""

import sys
import time

import cv2

import config
from detection.face_mesh import FaceMeshDetector
from detection.eye_detection import calculate_ear
from detection.yawn_detection import calculate_mar
from detection.head_pose import HeadPoseEstimator
from fatigue_logic import FatigueStateMachine
from logger import EventLogger
from alarm import AlarmManager
from utils.camera_utils import (
    is_valid_frame,
    FPSCounter,
    draw_landmarks_points,
    draw_state_border,
    draw_dashboard,
)


def open_camera() -> cv2.VideoCapture:
    """Open the configured camera with a stable backend for Windows."""
    backend = cv2.CAP_DSHOW if config.CAMERA_BACKEND_DSHOW else 0
    cap = cv2.VideoCapture(config.CAMERA_INDEX, backend)
    if config.FRAME_WIDTH:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    if config.FRAME_HEIGHT:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    return cap


def main() -> int:
    cap = open_camera()
    if not cap.isOpened():
        print("ERROR: Could not open webcam. Check camera permissions and "
              "that no other application is currently using it.")
        return 1

    try:
        face_mesh_detector = FaceMeshDetector()
        head_pose_estimator = HeadPoseEstimator()
        fatigue_engine = FatigueStateMachine()
    except Exception as exc:  # noqa: BLE001 - top-level init guard by design
        print(f"ERROR: Failed to initialize detection pipeline: {exc}")
        cap.release()
        return 1

    try:
        event_logger = EventLogger()
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: Could not initialize CSV logger ({exc}). Continuing without logging.")
        event_logger = None

    try:
        alarm_manager = AlarmManager()
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: Could not initialize audio alerts ({exc}). Continuing without sound.")
        alarm_manager = None

    fps_counter = FPSCounter()

    print("Automotive DMS running. Press 'q' to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret or not is_valid_frame(frame):
                continue

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            now = time.time()

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            landmarks = face_mesh_detector.process(rgb_frame)

            if landmarks is None:
                result = fatigue_engine.update_no_face(now)
            else:
                ear, left_pts, right_pts = calculate_ear(landmarks, w, h)
                mar, mouth_pts = calculate_mar(landmarks, w, h)
                success, pitch, yaw, roll = head_pose_estimator.estimate(landmarks, w, h)
                if not success:
                    pitch = yaw = roll = 0.0

                result = fatigue_engine.update(now, ear, mar, pitch, yaw, roll)

                draw_landmarks_points(frame, left_pts + right_pts, (0, 255, 0))
                draw_landmarks_points(frame, mouth_pts, (255, 0, 255))

            if event_logger is not None:
                event_logger.log_if_state_changed(result)
            if alarm_manager is not None:
                alarm_manager.trigger(result.state, now)

            fps = fps_counter.tick()
            draw_state_border(frame, result.state)
            draw_dashboard(frame, result, fps)

            cv2.imshow("Automotive DMS", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        face_mesh_detector.close()
        print("Shutdown complete.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
