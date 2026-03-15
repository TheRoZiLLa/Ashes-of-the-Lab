"""
entity_base.py - Abstract base class for all game entities.

Every entity in the world (player, enemy, projectile, etc.) inherits from
Entity. It provides:
  - world-space Rect (position + size)
  - floating-point velocity [vx, vy]
  - abstract update / draw interface
"""

import pygame
from abc import ABC, abstractmethod


class Entity(ABC):
    """
    Base class for all game entities.

    Parameters
    ----------
    x, y   : Top-left world position in pixels.
    width, height : Bounding box dimensions.
    color  : Draw colour (RGB tuple).
    """

    def __init__(self, x: float, y: float, width: int, height: int, color: tuple):
        # Store float position separately; Rect is kept in sync
        self._fx: float = float(x)
        self._fy: float = float(y)
        self.rect  = pygame.Rect(int(x), int(y), width, height)
        self.color = color

        # Physics state
        self.velocity: list = [0.0, 0.0]   # [vx, vy] px/s

        # Lifecycle flag – set True when this entity should be removed
        self.dead: bool = False

    # ── Derived position helpers ─────────────────────────────────────────────
    @property
    def x(self) -> float:
        return self._fx

    @x.setter
    def x(self, value: float):
        self._fx = value
        self.rect.x = int(value)

    @property
    def y(self) -> float:
        return self._fy

    @y.setter
    def y(self, value: float):
        self._fy = value
        self.rect.y = int(value)

    def sync_rect(self):
        """Push float position into the pygame Rect (call after physics)."""
        self._fx = float(self.rect.x)
        self._fy = float(self.rect.y)

    # ── Interface ────────────────────────────────────────────────────────────
    @abstractmethod
    def update(self, dt: float, **kwargs) -> None:
        """Update entity logic. `dt` is delta time in seconds."""

    @abstractmethod
    def draw(self, surface: pygame.Surface, camera) -> None:
        """Render the entity to `surface` using the camera offset."""

    # ── Convenience draw helper ──────────────────────────────────────────────
    def _draw_rect(self, surface: pygame.Surface, camera, color: tuple = None, border: int = 0) -> pygame.Rect:
        """Draw the entity's rect in screen space and return the screen rect."""
        screen_rect = camera.apply(self.rect)
        pygame.draw.rect(surface, color or self.color, screen_rect, border)
        return screen_rect
