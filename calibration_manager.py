"""
Calibration Manager - Veya
Maps eye coordinates to screen coordinates through calibration process.

Veya is an eye-tracking drawing application for people with motor disabilities.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from scipy.spatial import distance


class CalibrationPoint:
    """Represents a single calibration point."""

    def __init__(self, screen_x: int, screen_y: int):
        self.screen_pos = np.array([screen_x, screen_y], dtype=np.float32)
        self.eye_samples: List[np.ndarray] = []

    def add_sample(self, eye_x: float, eye_y: float):
        """Add an eye position sample for this calibration point."""
        self.eye_samples.append(np.array([eye_x, eye_y], dtype=np.float32))

    def get_average_eye_pos(self) -> Optional[np.ndarray]:
        """Get average of all eye samples."""
        if not self.eye_samples:
            return None
        return np.mean(self.eye_samples, axis=0)


class CalibrationManager:
    """
    Manages calibration process to map eye coordinates to screen coordinates.
    Uses polynomial transformation for accurate mapping.
    """

    def __init__(self, screen_width: int, screen_height: int):
        """
        Initialize calibration manager.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Calibration grid (9-point calibration by default)
        self.calibration_points: List[CalibrationPoint] = []
        self.is_calibrated = False

        # Transformation matrices
        self.transform_matrix: Optional[np.ndarray] = None

        # Calibration state
        self.current_point_index = 0
        self.samples_per_point = 30
        self.current_samples = 0

        # Initialize 9-point calibration grid
        self._init_calibration_grid()

    def _init_calibration_grid(self):
        """Initialize 9-point calibration grid."""
        margin_x = int(self.screen_width * 0.1)
        margin_y = int(self.screen_height * 0.1)

        positions = [
            (margin_x, margin_y),  # Top-left
            (self.screen_width // 2, margin_y),  # Top-center
            (self.screen_width - margin_x, margin_y),  # Top-right
            (margin_x, self.screen_height // 2),  # Middle-left
            (self.screen_width // 2, self.screen_height // 2),  # Center
            (self.screen_width - margin_x, self.screen_height // 2),  # Middle-right
            (margin_x, self.screen_height - margin_y),  # Bottom-left
            (self.screen_width // 2, self.screen_height - margin_y),  # Bottom-center
            (self.screen_width - margin_x, self.screen_height - margin_y),  # Bottom-right
        ]

        self.calibration_points = [CalibrationPoint(x, y) for x, y in positions]

    def reset(self):
        """Reset calibration state."""
        self.is_calibrated = False
        self.current_point_index = 0
        self.current_samples = 0
        self.transform_matrix = None
        for point in self.calibration_points:
            point.eye_samples.clear()

    def is_calibration_complete(self) -> bool:
        """Check if calibration is complete."""
        return self.is_calibrated

    def get_current_calibration_point(self) -> Optional[Tuple[int, int]]:
        """
        Get current calibration point screen position.

        Returns:
            (x, y) tuple or None if calibration is complete
        """
        if self.current_point_index >= len(self.calibration_points):
            return None
        point = self.calibration_points[self.current_point_index]
        return tuple(point.screen_pos.astype(int))

    def add_calibration_sample(self, eye_x: float, eye_y: float) -> bool:
        """
        Add a calibration sample for the current point.

        Args:
            eye_x: Eye x coordinate
            eye_y: Eye y coordinate

        Returns:
            True if moved to next point or completed calibration
        """
        if self.current_point_index >= len(self.calibration_points):
            return False

        point = self.calibration_points[self.current_point_index]
        point.add_sample(eye_x, eye_y)
        self.current_samples += 1

        # Move to next point when enough samples collected
        if self.current_samples >= self.samples_per_point:
            self.current_point_index += 1
            self.current_samples = 0

            # If all points calibrated, compute transformation
            if self.current_point_index >= len(self.calibration_points):
                self._compute_calibration()
                return True

            return True

        return False

    def _compute_calibration(self):
        """Compute transformation from eye coordinates to screen coordinates."""
        eye_points = []
        screen_points = []

        for point in self.calibration_points:
            avg_eye = point.get_average_eye_pos()
            if avg_eye is not None:
                eye_points.append(avg_eye)
                screen_points.append(point.screen_pos)

        if len(eye_points) < 4:
            print("Error: Not enough calibration points")
            return

        eye_points = np.array(eye_points, dtype=np.float32)
        screen_points = np.array(screen_points, dtype=np.float32)

        # Use polynomial transformation (affine or perspective)
        # For better accuracy, we use perspective transform
        if len(eye_points) >= 4:
            # Find homography matrix (perspective transform)
            self.transform_matrix, _ = cv2.findHomography(eye_points, screen_points)
            self.is_calibrated = True
            print("Calibration complete!")
        else:
            print("Error: Need at least 4 points for calibration")

    def map_to_screen(self, eye_x: float, eye_y: float) -> Optional[Tuple[int, int]]:
        """
        Map eye coordinates to screen coordinates.

        Args:
            eye_x: Eye x coordinate
            eye_y: Eye y coordinate

        Returns:
            (screen_x, screen_y) tuple or None if not calibrated
        """
        if not self.is_calibrated or self.transform_matrix is None:
            return None

        # Apply homography transformation
        eye_point = np.array([[[eye_x, eye_y]]], dtype=np.float32)
        screen_point = cv2.perspectiveTransform(eye_point, self.transform_matrix)

        x, y = screen_point[0][0]

        # Clamp to screen bounds
        x = int(np.clip(x, 0, self.screen_width - 1))
        y = int(np.clip(y, 0, self.screen_height - 1))

        return (x, y)

    def draw_calibration_ui(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw calibration UI on frame.

        Args:
            frame: Input frame

        Returns:
            Frame with calibration UI
        """
        ui_frame = frame.copy()

        # Draw all calibration points
        for i, point in enumerate(self.calibration_points):
            x, y = point.screen_pos.astype(int)

            if i < self.current_point_index:
                # Already calibrated - green
                color = (0, 255, 0)
                cv2.circle(ui_frame, (x, y), 8, color, -1)
            elif i == self.current_point_index:
                # Current point - red with animation
                color = (0, 0, 255)
                radius = 20 + int(10 * np.sin(cv2.getTickCount() / 1000))
                cv2.circle(ui_frame, (x, y), radius, color, 2)
                cv2.circle(ui_frame, (x, y), 5, color, -1)

                # Progress bar
                progress = self.current_samples / self.samples_per_point
                bar_width = 100
                bar_height = 10
                bar_x = x - bar_width // 2
                bar_y = y + 40

                cv2.rectangle(ui_frame, (bar_x, bar_y),
                            (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 1)
                cv2.rectangle(ui_frame, (bar_x, bar_y),
                            (bar_x + int(bar_width * progress), bar_y + bar_height),
                            (0, 255, 0), -1)
            else:
                # Not yet calibrated - white
                color = (255, 255, 255)
                cv2.circle(ui_frame, (x, y), 8, color, 1)

        # Instructions
        if self.current_point_index < len(self.calibration_points):
            text = f"Look at the RED circle ({self.current_point_index + 1}/{len(self.calibration_points)})"
            cv2.putText(ui_frame, text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(ui_frame, "Keep looking until it turns green",
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        else:
            cv2.putText(ui_frame, "Calibration Complete!",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return ui_frame

    def get_calibration_progress(self) -> float:
        """
        Get overall calibration progress.

        Returns:
            Progress from 0.0 to 1.0
        """
        if len(self.calibration_points) == 0:
            return 0.0

        completed = self.current_point_index
        current_progress = self.current_samples / self.samples_per_point

        total_progress = (completed + current_progress) / len(self.calibration_points)
        return min(total_progress, 1.0)


if __name__ == "__main__":
    # Test calibration manager
    import time

    cal = CalibrationManager(800, 600)

    print("Calibration test")
    print(f"Total points: {len(cal.calibration_points)}")

    # Simulate calibration
    for i in range(len(cal.calibration_points)):
        point = cal.get_current_calibration_point()
        print(f"Calibrating point {i + 1}: {point}")

        # Simulate eye samples (add some noise)
        for _ in range(cal.samples_per_point):
            eye_x = point[0] + np.random.normal(0, 5)
            eye_y = point[1] + np.random.normal(0, 5)
            cal.add_calibration_sample(eye_x, eye_y)

    print(f"Calibrated: {cal.is_calibrated}")

    # Test mapping
    if cal.is_calibrated:
        test_eye = (400, 300)
        screen_pos = cal.map_to_screen(test_eye[0], test_eye[1])
        print(f"Eye {test_eye} -> Screen {screen_pos}")
