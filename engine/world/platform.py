"""
platform.py - Solid rectangular platform for the level.

Platforms are pure data (just a Rect + colour). They participate in
collision resolution but have no logic of their own.
"""

import pygame
from engine.settings import COL_PLATFORM


class Platform:
    """
    A static, solid rectangle in world space.

    Parameters
    ----------
    x, y          : Top-left world position.
    width, height : Dimensions in pixels.
    color         : Draw colour (defaults to global platform colour).
    """

    def __init__(self, x: int, y: int, width: int, height: int, color: tuple = None):
        self.rect  = pygame.Rect(x, y, width, height)
        self.color = color or COL_PLATFORM

    # ── Draw ─────────────────────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface, camera) -> None:
        screen_rect = camera.apply(self.rect)
        pygame.draw.rect(surface, self.color, screen_rect)

        # Subtle top edge highlight for readability
        highlight = tuple(min(255, c + 40) for c in self.color)
        pygame.draw.line(
            surface, highlight,
            screen_rect.topleft, screen_rect.topright, 2
        )
