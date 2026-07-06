"""
Veya - Eye Tracking Drawing Application
Main application integrating eye tracking, calibration, and drawing.

Veya is an eye-tracking drawing application that empowers people with motor
disabilities to create art and control computers using only their eye movements.
"""

import pygame
import sys
import cv2
import numpy as np
from typing import Optional
from enum import Enum

from eye_tracker import EyeTracker
from calibration_manager import CalibrationManager
from drawing_canvas import DrawingCanvas


class AppMode(Enum):
    """Application modes."""
    CALIBRATION = 0
    DRAWING = 1


class VeyaApp:
    """Main application class."""

    def __init__(self, screen_width: int = 1024, screen_height: int = 768):
        """
        Initialize Veya application.

        Args:
            screen_width: Window width
            screen_height: Window height
        """
        # Initialize pygame
        pygame.init()

        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Veya - Eye Tracking Drawing")

        self.clock = pygame.time.Clock()
        self.fps = 30

        # Initialize components
        self.eye_tracker = EyeTracker()
        self.calibration_manager = CalibrationManager(screen_width, screen_height)
        self.canvas = DrawingCanvas(screen_width, screen_height)

        # App state
        self.mode = AppMode.CALIBRATION
        self.running = False
        self.paused = False

        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)

        # Eye tracking overlay
        self.show_eye_preview = True
        self.eye_preview_size = (320, 240)

    def start(self) -> bool:
        """Start the application."""
        if not self.eye_tracker.start():
            print("Failed to start eye tracker")
            return False

        self.running = True
        return True

    def stop(self):
        """Stop the application."""
        self.running = False
        self.eye_tracker.stop()
        pygame.quit()

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                elif event.key == pygame.K_TAB:
                    # Switch modes
                    if self.mode == AppMode.CALIBRATION:
                        if self.calibration_manager.is_calibrated:
                            self.mode = AppMode.DRAWING
                    else:
                        self.mode = AppMode.CALIBRATION

                elif event.key == pygame.K_r:
                    # Reset calibration
                    self.calibration_manager.reset()
                    self.mode = AppMode.CALIBRATION

                elif event.key == pygame.K_p:
                    # Toggle pause
                    self.paused = not self.paused

                elif event.key == pygame.K_e:
                    # Toggle eye preview
                    self.show_eye_preview = not self.show_eye_preview

                # Drawing mode shortcuts
                elif self.mode == AppMode.DRAWING:
                    if event.key == pygame.K_u:
                        self.canvas.undo()
                    elif event.key == pygame.K_c:
                        self.canvas.clear()
                    elif event.key == pygame.K_g:
                        self.canvas.toggle_grid()
                    elif event.key == pygame.K_s:
                        # Save drawing
                        import datetime
                        filename = f"drawing_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        self.canvas.save_image(filename)

    def update(self):
        """Update application state."""
        if self.paused:
            return

        # Update eye tracker
        if not self.eye_tracker.update():
            return

        gaze = self.eye_tracker.get_gaze_point()
        if gaze is None:
            return

        current_time = pygame.time.get_ticks() / 1000.0

        if self.mode == AppMode.CALIBRATION:
            # Calibration mode
            if not self.calibration_manager.is_calibration_complete():
                # Add calibration sample
                moved = self.calibration_manager.add_calibration_sample(gaze[0], gaze[1])

                # Auto-switch to drawing when calibration complete
                if self.calibration_manager.is_calibrated:
                    self.mode = AppMode.DRAWING

        elif self.mode == AppMode.DRAWING:
            # Drawing mode
            if self.calibration_manager.is_calibrated:
                # Map gaze to screen coordinates
                screen_pos = self.calibration_manager.map_to_screen(gaze[0], gaze[1])

                if screen_pos:
                    self.canvas.update_cursor(screen_pos[0], screen_pos[1])

                    # Check for dwell to activate drawing
                    if self.canvas.check_dwell(current_time):
                        if self.canvas.draw_mode.value == 0:  # NONE
                            self.canvas.start_drawing()
                        else:
                            self.canvas.end_stroke()

                    # Add point if drawing
                    if self.canvas.draw_mode.value == 1:  # DRAWING
                        self.canvas.add_point()

    def draw(self):
        """Render frame."""
        self.screen.fill((40, 40, 40))

        current_time = pygame.time.get_ticks() / 1000.0

        if self.mode == AppMode.CALIBRATION:
            self._draw_calibration_mode()
        elif self.mode == AppMode.DRAWING:
            self._draw_drawing_mode(current_time)

        # Draw eye preview
        if self.show_eye_preview:
            self._draw_eye_preview()

        # Draw status bar
        self._draw_status_bar()

        pygame.display.flip()

    def _draw_calibration_mode(self):
        """Draw calibration UI."""
        # Get camera frame
        frame = self.eye_tracker.get_frame()
        if frame is not None:
            # Convert to pygame surface
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (self.screen_width, self.screen_height))
            frame_surface = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))

            # Draw calibration UI on frame
            calib_array = pygame.surfarray.array3d(frame_surface)
            calib_array = calib_array.swapaxes(0, 1)
            calib_array = self.calibration_manager.draw_calibration_ui(calib_array)
            calib_surface = pygame.surfarray.make_surface(calib_array.swapaxes(0, 1))

            self.screen.blit(calib_surface, (0, 0))

        # Instructions
        if self.calibration_manager.is_calibrated:
            text = self.font_large.render("Calibration Complete!", True, (0, 255, 0))
            self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, 100))

            text = self.font_medium.render("Press TAB to start drawing", True, (255, 255, 255))
            self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, 160))

    def _draw_drawing_mode(self, current_time: float):
        """Draw drawing UI."""
        # Render canvas
        canvas_surface = self.canvas.render()
        self.screen.blit(canvas_surface, (0, 0))

        # Draw cursor
        self.canvas.draw_cursor(self.screen, current_time)

        # Draw stats
        stats_y = self.screen_height - 40
        stats_text = f"Strokes: {self.canvas.get_stroke_count()} | Points: {self.canvas.get_total_points()}"
        text = self.font_small.render(stats_text, True, (100, 100, 100))
        self.screen.blit(text, (10, stats_y))

    def _draw_eye_preview(self):
        """Draw eye tracking preview."""
        frame = self.eye_tracker.get_frame()
        if frame is None:
            return

        # Draw debug overlay
        debug_frame = self.eye_tracker.draw_debug(frame)

        # Resize for preview
        preview = cv2.resize(debug_frame, self.eye_preview_size)
        preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        preview_surface = pygame.surfarray.make_surface(preview_rgb.swapaxes(0, 1))

        # Draw in corner with border
        x = self.screen_width - self.eye_preview_size[0] - 20
        y = 20

        pygame.draw.rect(self.screen, (255, 255, 255),
                        (x - 2, y - 2, self.eye_preview_size[0] + 4, self.eye_preview_size[1] + 4), 2)
        self.screen.blit(preview_surface, (x, y))

    def _draw_status_bar(self):
        """Draw status bar."""
        # Background
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, self.screen_width, 35))

        # Mode
        mode_text = f"Mode: {'CALIBRATION' if self.mode == AppMode.CALIBRATION else 'DRAWING'}"
        text = self.font_small.render(mode_text, True, (255, 255, 255))
        self.screen.blit(text, (10, 8))

        # FPS
        fps_text = f"FPS: {int(self.clock.get_fps())}"
        text = self.font_small.render(fps_text, True, (200, 200, 200))
        self.screen.blit(text, (self.screen_width - 100, 8))

        # Shortcuts (if in drawing mode)
        if self.mode == AppMode.DRAWING:
            shortcuts = "U: undo | C: clear | G: grid | S: save | TAB: recalibrate"
            text = self.font_small.render(shortcuts, True, (150, 150, 150))
            self.screen.blit(text, (200, 8))

    def run(self):
        """Main application loop."""
        if not self.start():
            return

        print("Veya started")
        print("Controls:")
        print("  TAB - Switch between calibration and drawing")
        print("  R - Reset calibration")
        print("  P - Pause/unpause")
        print("  E - Toggle eye preview")
        print("  U - Undo last stroke")
        print("  C - Clear canvas")
        print("  G - Toggle grid")
        print("  S - Save drawing")
        print("  ESC - Exit")

        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.fps)

        self.stop()


def main():
    """Entry point."""
    app = VeyaApp(1024, 768)
    app.run()


if __name__ == "__main__":
    main()
