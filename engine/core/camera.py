"""
camera.py - Smooth-follow camera system.

The camera translates world coordinates to screen coordinates so that
the player always stays near the centre of the screen while the level
scrolls behind them. Clamped to level bounds so dead edges never show.
"""

import pygame
import math
from engine.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CAMERA_SMOOTHING,
    CAMERA_LOOKAHEAD_X, CAMERA_LOOKAHEAD_Y_UP, CAMERA_LOOKAHEAD_Y_DOWN,
    CAMERA_DASH_OFFSET, CAMERA_FOLLOW_INTENSITY
)


class Camera:
    """
    Tracks a target entity and produces a world→screen offset.

    Parameters
    ----------
    level_width  : total pixel width of the level
    level_height : total pixel height of the level
    viewport_width : width of the screen or rendering surface
    viewport_height : height of the screen or rendering surface
    """

    def __init__(self, level_width: int, level_height: int, viewport_width: int = SCREEN_WIDTH, viewport_height: int = SCREEN_HEIGHT):
        self.level_width  = level_width
        self.level_height = level_height
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        # Floating-point camera position (top-left corner in world space)
        self._x = 0.0
        self._y = 0.0

        self.dx = 0.0
        self.dy = 0.0

        self._shake_duration = 0.0
        self._shake_elapsed = 0.0
        self._shake_magnitude = 0.0
        self.shake_offset_x = 0
        self.shake_offset_y = 0

    def start_shake(self, duration: float, magnitude: float) -> None:
        self._shake_duration = duration
        self._shake_elapsed = 0.0
        self._shake_magnitude = magnitude

    # ── Update ───────────────────────────────────────────────────────────────
    def update(self, target_rect: pygame.Rect, dt: float, facing: int = 1, velocity: list = [0, 0], is_dashing: bool = False, ambient_shake: float = 0.0) -> None:
        """Smoothly move the camera so `target_rect` is centred on screen with state-based offset."""
        if self._shake_elapsed < self._shake_duration:
            self._shake_elapsed += dt
            t = 1.0 - (self._shake_elapsed / self._shake_duration)
            amp = self._shake_magnitude * t
            angle = self._shake_elapsed * 60 * math.pi
            self.shake_offset_x = int(amp * math.sin(angle))
            self.shake_offset_y = int(amp * math.cos(angle * 0.7))
        else:
            self.shake_offset_x = 0
            self.shake_offset_y = 0

        if ambient_shake > 0:
            # Subtle high-frequency vibration for critical states
            now = pygame.time.get_ticks() / 1000.0
            self.shake_offset_x += int(math.sin(now * 80) * ambient_shake)
            self.shake_offset_y += int(math.cos(now * 95) * (ambient_shake * 0.8))

        offset_x = CAMERA_LOOKAHEAD_X * facing
        if is_dashing:
            offset_x += CAMERA_DASH_OFFSET * facing

        offset_y = 0
        if velocity[1] > 200:
            offset_y += CAMERA_LOOKAHEAD_Y_DOWN
        elif velocity[1] < -200:
            offset_y -= CAMERA_LOOKAHEAD_Y_UP

        # Apply motion sickness intensity setting
        offset_x *= CAMERA_FOLLOW_INTENSITY
        offset_y *= CAMERA_FOLLOW_INTENSITY

        # Desired top-left so target is screen-centred
        target_x = target_rect.centerx - self.viewport_width  // 2 + offset_x
        target_y = target_rect.centery - self.viewport_height // 2 + offset_y

        # Exponential smoothing (framerate-independent lerp)
        t = 1.0 - (1.0 / (1.0 + CAMERA_SMOOTHING * dt))
        old_x, old_y = self._x, self._y
        self._x += (target_x - self._x) * t
        self._y += (target_y - self._y) * t

        # Clamp so we never reveal space outside the level
        self._x = max(0, min(self._x, self.level_width  - self.viewport_width))
        self._y = max(0, min(self._y, self.level_height - self.viewport_height))

        self.dx = self._x - old_x
        self.dy = self._y - old_y

    # ── Coordinate helpers ──────────────────────────────────────────────────
    def apply(self, world_rect: pygame.Rect) -> pygame.Rect:
        """Return a new Rect shifted into screen space."""
        return world_rect.move(-int(self._x) + self.shake_offset_x, -int(self._y) + self.shake_offset_y)

    def apply_point(self, wx: float, wy: float) -> tuple:
        """Convert a world-space point to screen-space."""
        return (wx - self._x + self.shake_offset_x, wy - self._y + self.shake_offset_y)

    @property
    def offset_x(self) -> float:
        return self._x

    @property
    def offset_y(self) -> float:
        return self._y
