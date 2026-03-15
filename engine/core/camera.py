"""
camera.py - Smooth-follow camera system.

The camera translates world coordinates to screen coordinates so that
the player always stays near the centre of the screen while the level
scrolls behind them. Clamped to level bounds so dead edges never show.
"""

import pygame
from engine.settings import SCREEN_WIDTH, SCREEN_HEIGHT, CAMERA_SMOOTHING


class Camera:
    """
    Tracks a target entity and produces a world→screen offset.

    Parameters
    ----------
    level_width  : total pixel width of the level
    level_height : total pixel height of the level
    """

    def __init__(self, level_width: int, level_height: int):
        self.level_width  = level_width
        self.level_height = level_height

        # Floating-point camera position (top-left corner in world space)
        self._x = 0.0
        self._y = 0.0

    # ── Update ───────────────────────────────────────────────────────────────
    def update(self, target_rect: pygame.Rect, dt: float) -> None:
        """Smoothly move the camera so `target_rect` is centred on screen."""
        # Desired top-left so target is screen-centred
        target_x = target_rect.centerx - SCREEN_WIDTH  // 2
        target_y = target_rect.centery - SCREEN_HEIGHT // 2

        # Exponential smoothing (framerate-independent lerp)
        t = 1.0 - (1.0 / (1.0 + CAMERA_SMOOTHING * dt))
        self._x += (target_x - self._x) * t
        self._y += (target_y - self._y) * t

        # Clamp so we never reveal space outside the level
        self._x = max(0, min(self._x, self.level_width  - SCREEN_WIDTH))
        self._y = max(0, min(self._y, self.level_height - SCREEN_HEIGHT))

    # ── Coordinate helpers ──────────────────────────────────────────────────
    def apply(self, world_rect: pygame.Rect) -> pygame.Rect:
        """Return a new Rect shifted into screen space."""
        return world_rect.move(-int(self._x), -int(self._y))

    def apply_point(self, wx: float, wy: float) -> tuple:
        """Convert a world-space point to screen-space."""
        return (wx - self._x, wy - self._y)

    @property
    def offset_x(self) -> float:
        return self._x

    @property
    def offset_y(self) -> float:
        return self._y
