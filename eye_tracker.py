"""
Eye Tracker Module - Veya
Detects and tracks eye movements using computer vision.
Port from EyeWriter C++ to Python.

Veya is an eye-tracking drawing application for people with motor disabilities.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, Tuple, List


class EyeTracker:
    """
    Main eye tracking class.
    Detects eye position, pupil, and calculates gaze direction.
    """

    def __init__(self, camera_id: int = 0):
        """
        Initialize eye tracker.

        Args:
            camera_id: Camera device ID (default 0 for built-in webcam)
        """
        self.camera_id = camera_id
        self.cap: Optional[cv2.VideoCapture] = None

        # MediaPipe Face Mesh for eye tracking
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Tracking state
        self.eye_found = False
        self.pupil_found = False
        self.current_frame: Optional[np.ndarray] = None
        self.gray_frame: Optional[np.ndarray] = None

        # Eye landmarks indices (MediaPipe Face Mesh)
        # Left eye: 468-473 (iris), Right eye: 473-478 (iris)
        self.LEFT_IRIS = [468, 469, 470, 471, 472]
        self.RIGHT_IRIS = [473, 474, 475, 476, 477]

        # Eye contours
        self.LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]

        # Current eye position
        self.left_eye_center: Optional[Tuple[float, float]] = None
        self.right_eye_center: Optional[Tuple[float, float]] = None
        self.gaze_point: Optional[Tuple[float, float]] = None

        # Smoothing
        self.smooth_factor = 0.7
        self.smoothed_gaze: Optional[np.ndarray] = None

    def start(self) -> bool:
        """Start video capture."""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"Error: Could not open camera {self.camera_id}")
            return False

        # Set camera properties for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        return True

    def stop(self):
        """Stop video capture and release resources."""
        if self.cap:
            self.cap.release()
        self.face_mesh.close()

    def update(self) -> bool:
        """
        Update tracking by processing next frame.

        Returns:
            True if frame was successfully processed
        """
        if not self.cap:
            return False

        ret, frame = self.cap.read()
        if not ret:
            return False

        self.current_frame = frame
        self.gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Flip frame horizontally for mirror view
        self.current_frame = cv2.flip(self.current_frame, 1)

        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)

        # Process frame with MediaPipe
        results = self.face_mesh.process(rgb_frame)

        self.eye_found = False
        self.pupil_found = False

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            h, w = self.current_frame.shape[:2]

            # Get iris landmarks
            left_iris_coords = []
            right_iris_coords = []

            for idx in self.LEFT_IRIS:
                landmark = face_landmarks.landmark[idx]
                x, y = int(landmark.x * w), int(landmark.y * h)
                left_iris_coords.append((x, y))

            for idx in self.RIGHT_IRIS:
                landmark = face_landmarks.landmark[idx]
                x, y = int(landmark.x * w), int(landmark.y * h)
                right_iris_coords.append((x, y))

            # Calculate eye centers
            if left_iris_coords:
                self.left_eye_center = np.mean(left_iris_coords, axis=0)
                self.eye_found = True
                self.pupil_found = True

            if right_iris_coords:
                self.right_eye_center = np.mean(right_iris_coords, axis=0)
                self.eye_found = True
                self.pupil_found = True

            # Calculate average gaze point (between both eyes)
            if self.left_eye_center is not None and self.right_eye_center is not None:
                gaze = (self.left_eye_center + self.right_eye_center) / 2

                # Apply smoothing
                if self.smoothed_gaze is None:
                    self.smoothed_gaze = gaze
                else:
                    self.smoothed_gaze = (self.smooth_factor * self.smoothed_gaze +
                                         (1 - self.smooth_factor) * gaze)

                self.gaze_point = tuple(self.smoothed_gaze.astype(int))

        return True

    def get_gaze_point(self) -> Optional[Tuple[int, int]]:
        """
        Get current smoothed gaze point in camera coordinates.

        Returns:
            (x, y) tuple or None if no eyes detected
        """
        return self.gaze_point

    def get_eye_centers(self) -> Tuple[Optional[Tuple[float, float]], Optional[Tuple[float, float]]]:
        """
        Get raw eye center positions.

        Returns:
            Tuple of (left_eye_center, right_eye_center)
        """
        return self.left_eye_center, self.right_eye_center

    def draw_debug(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw debug visualization on frame.

        Args:
            frame: Input frame

        Returns:
            Frame with debug overlay
        """
        debug_frame = frame.copy()

        # Draw eye centers
        if self.left_eye_center is not None:
            cv2.circle(debug_frame, tuple(self.left_eye_center.astype(int)), 3, (0, 255, 0), -1)
            cv2.putText(debug_frame, "L", tuple(self.left_eye_center.astype(int)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        if self.right_eye_center is not None:
            cv2.circle(debug_frame, tuple(self.right_eye_center.astype(int)), 3, (0, 255, 0), -1)
            cv2.putText(debug_frame, "R", tuple(self.right_eye_center.astype(int)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Draw gaze point
        if self.gaze_point is not None:
            cv2.circle(debug_frame, self.gaze_point, 5, (0, 0, 255), 2)
            cv2.line(debug_frame, self.gaze_point,
                    (self.gaze_point[0], self.gaze_point[1] + 30), (0, 0, 255), 2)

        # Status text
        status = "Eye: " + ("YES" if self.eye_found else "NO")
        status += " | Pupil: " + ("YES" if self.pupil_found else "NO")
        cv2.putText(debug_frame, status, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return debug_frame

    def get_frame(self) -> Optional[np.ndarray]:
        """Get current frame."""
        return self.current_frame


if __name__ == "__main__":
    # Test eye tracker
    tracker = EyeTracker()

    if not tracker.start():
        print("Failed to start tracker")
        exit(1)

    print("Eye tracker started. Press 'q' to quit.")

    try:
        while True:
            if tracker.update():
                frame = tracker.get_frame()
                if frame is not None:
                    debug_frame = tracker.draw_debug(frame)
                    cv2.imshow("Eye Tracker Debug", debug_frame)

                    gaze = tracker.get_gaze_point()
                    if gaze:
                        print(f"Gaze: {gaze}")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        tracker.stop()
        cv2.destroyAllWindows()
