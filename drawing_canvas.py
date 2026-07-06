"""
Drawing Scene - Veya
Main drawing interface with eye-controlled cursor.

Veya is an eye-tracking drawing application for people with motor disabilities.
"""

import pygame
import numpy as np
from typing import List, Tuple, Optional
from enum import Enum


class DrawMode(Enum):
    """Drawing modes."""
    NONE = 0
    DRAWING = 1
    PAUSED = 2


class Stroke:
    """Represents a single continuous stroke."""

    def __init__(self, color: Tuple[int, int, int] = (0, 0, 0), thickness: int = 3):
        self.points: List[Tuple[int, int]] = []
        self.color = color
        self.thickness = thickness

    def add_point(self, x: int, y: int):
        """Add a point to the stroke."""
        self.points.append((x, y))

    def draw(self, surface: pygame.Surface):
        """Draw the stroke on a surface."""
        if len(self.points) < 2:
            return

        pygame.draw.lines(surface, self.color, False, self.points, self.thickness)


class DrawingCanvas:
    """Main drawing canvas with eye-controlled cursor."""

    def __init__(self, width: int, height: int):
        """
        Initialize drawing canvas.

        Args:
            width: Canvas width
            height: Canvas height
        """
        self.width = width
        self.height = height

        # Canvas surface
        self.canvas = pygame.Surface((width, height))
        self.canvas.fill((255, 255, 255))

        # Drawing state
        self.strokes: List[Stroke] = []
        self.current_stroke: Optional[Stroke] = None
        self.draw_mode = DrawMode.NONE

        # Cursor position
        self.cursor_x = width // 2
        self.cursor_y = height // 2

        # Dwell time for activation (seconds)
        self.dwell_time = 1.5
        self.dwell_threshold = 15  # pixels - how close cursor must stay
        self.dwell_start_time: Optional[float] = None
        self.dwell_start_pos: Optional[Tuple[int, int]] = None

        # Drawing settings
        self.draw_color = (0, 0, 0)
        self.draw_thickness = 3

        # Grid
        self.show_grid = False
        self.grid_spacing = 20

    def update_cursor(self, x: int, y: int):
        """
        Update cursor position from gaze coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.cursor_x = x
        self.cursor_y = y

    def check_dwell(self, current_time: float) -> bool:
        """
        Check if cursor has dwelled long enough to trigger action.

        Args:
            current_time: Current time in seconds

        Returns:
            True if dwell completed
        """
        # Start dwell if not started
        if self.dwell_start_time is None:
            self.dwell_start_time = current_time
            self.dwell_start_pos = (self.cursor_x, self.cursor_y)
            return False

        # Check if cursor moved too much
        if self.dwell_start_pos is not None:
            dx = self.cursor_x - self.dwell_start_pos[0]
            dy = self.cursor_y - self.dwell_start_pos[1]
            distance = np.sqrt(dx * dx + dy * dy)

            if distance > self.dwell_threshold:
                # Reset dwell
                self.dwell_start_time = current_time
                self.dwell_start_pos = (self.cursor_x, self.cursor_y)
                return False

        # Check if enough time passed
        elapsed = current_time - self.dwell_start_time
        if elapsed >= self.dwell_time:
            self.dwell_start_time = None
            self.dwell_start_pos = None
            return True

        return False

    def get_dwell_progress(self, current_time: float) -> float:
        """
        Get dwell progress (0.0 to 1.0).

        Args:
            current_time: Current time in seconds

        Returns:
            Progress from 0.0 to 1.0
        """
        if self.dwell_start_time is None:
            return 0.0

        elapsed = current_time - self.dwell_start_time
        return min(elapsed / self.dwell_time, 1.0)

    def start_drawing(self):
        """Start a new stroke."""
        self.current_stroke = Stroke(self.draw_color, self.draw_thickness)
        self.draw_mode = DrawMode.DRAWING

    def add_point(self):
        """Add current cursor position to stroke."""
        if self.current_stroke is not None and self.draw_mode == DrawMode.DRAWING:
            self.current_stroke.add_point(self.cursor_x, self.cursor_y)

    def end_stroke(self):
        """Finish current stroke."""
        if self.current_stroke is not None:
            if len(self.current_stroke.points) > 1:
                self.strokes.append(self.current_stroke)
            self.current_stroke = None
            self.draw_mode = DrawMode.NONE

    def undo(self):
        """Undo last stroke."""
        if self.strokes:
            self.strokes.pop()

    def undo_point(self):
        """Remove last point from current stroke."""
        if self.current_stroke is not None and self.current_stroke.points:
            self.current_stroke.points.pop()

    def clear(self):
        """Clear all strokes."""
        self.strokes.clear()
        self.current_stroke = None
        self.draw_mode = DrawMode.NONE
        self.canvas.fill((255, 255, 255))

    def toggle_grid(self):
        """Toggle grid visibility."""
        self.show_grid = not self.show_grid

    def render(self) -> pygame.Surface:
        """
        Render canvas with all strokes.

        Returns:
            Rendered surface
        """
        # Clear canvas
        self.canvas.fill((255, 255, 255))

        # Draw grid if enabled
        if self.show_grid:
            grid_color = (220, 220, 220)
            for x in range(0, self.width, self.grid_spacing):
                pygame.draw.line(self.canvas, grid_color, (x, 0), (x, self.height), 1)
            for y in range(0, self.height, self.grid_spacing):
                pygame.draw.line(self.canvas, grid_color, (0, y), (self.width, y), 1)

        # Draw all completed strokes
        for stroke in self.strokes:
            stroke.draw(self.canvas)

        # Draw current stroke
        if self.current_stroke is not None:
            self.current_stroke.draw(self.canvas)

            # Draw line from last point to cursor
            if self.current_stroke.points:
                last_point = self.current_stroke.points[-1]
                pygame.draw.line(self.canvas, (200, 200, 200),
                               last_point, (self.cursor_x, self.cursor_y), 1)

        return self.canvas

    def draw_cursor(self, surface: pygame.Surface, current_time: float):
        """
        Draw cursor and dwell indicator.

        Args:
            surface: Surface to draw on
            current_time: Current time for dwell animation
        """
        # Draw cursor
        cursor_color = (255, 0, 0) if self.draw_mode == DrawMode.DRAWING else (100, 100, 255)
        pygame.draw.circle(surface, cursor_color, (self.cursor_x, self.cursor_y), 8, 2)

        # Draw dwell progress indicator
        if self.dwell_start_time is not None:
            progress = self.get_dwell_progress(current_time)
            if progress > 0:
                # Draw progress arc
                radius = 15
                angle = int(360 * progress)
                rect = pygame.Rect(self.cursor_x - radius, self.cursor_y - radius,
                                 radius * 2, radius * 2)

                # Draw arc segments
                if angle > 0:
                    points = []
                    points.append((self.cursor_x, self.cursor_y))
                    for i in range(0, angle + 1, 5):
                        rad = np.radians(i - 90)
                        x = self.cursor_x + radius * np.cos(rad)
                        y = self.cursor_y + radius * np.sin(rad)
                        points.append((int(x), int(y)))

                    if len(points) > 2:
                        pygame.draw.polygon(surface, (0, 255, 0, 100), points)
                        pygame.draw.lines(surface, (0, 200, 0), False, points[1:], 2)

    def save_image(self, filename: str):
        """
        Save canvas to image file.

        Args:
            filename: Output filename
        """
        pygame.image.save(self.canvas, filename)
        print(f"Canvas saved to {filename}")

    def get_stroke_count(self) -> int:
        """Get number of strokes."""
        return len(self.strokes)

    def get_total_points(self) -> int:
        """Get total number of points across all strokes."""
        total = sum(len(stroke.points) for stroke in self.strokes)
        if self.current_stroke:
            total += len(self.current_stroke.points)
        return total


if __name__ == "__main__":
    # Test drawing canvas
    pygame.init()

    canvas = DrawingCanvas(800, 600)
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Drawing Canvas Test")
    clock = pygame.time.Clock()

    running = True
    while running:
        current_time = pygame.time.get_ticks() / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if canvas.draw_mode == DrawMode.NONE:
                        canvas.start_drawing()
                    else:
                        canvas.end_stroke()
                elif event.key == pygame.K_u:
                    canvas.undo()
                elif event.key == pygame.K_c:
                    canvas.clear()
                elif event.key == pygame.K_g:
                    canvas.toggle_grid()

        # Update cursor from mouse (for testing)
        mx, my = pygame.mouse.get_pos()
        canvas.update_cursor(mx, my)

        # Add point if drawing
        if canvas.draw_mode == DrawMode.DRAWING:
            canvas.add_point()

        # Render
        canvas_surface = canvas.render()
        screen.blit(canvas_surface, (0, 0))
        canvas.draw_cursor(screen, current_time)

        # Status
        font = pygame.font.Font(None, 24)
        status = f"Strokes: {canvas.get_stroke_count()} | Points: {canvas.get_total_points()}"
        text = font.render(status, True, (0, 0, 0))
        screen.blit(text, (10, 10))

        instructions = font.render("SPACE: start/stop | U: undo | C: clear | G: grid", True, (100, 100, 100))
        screen.blit(instructions, (10, 580))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
