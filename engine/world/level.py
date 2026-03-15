"""
level.py - Defines and manages the demo level layout.

The level contains:
  - a list of Platform objects (static colliders + visual tiles)
  - a list of Zombie enemies (spawned at defined positions)
  - level dimensions (wider than the screen for camera scrolling)

The Game object uses level.platforms and level.enemies each frame.
"""

import pygame
from engine.world.platform import Platform
from engine.entities.enemy import Zombie
from engine.settings import SCREEN_WIDTH, SCREEN_HEIGHT


# ── Level dimensions ─────────────────────────────────────────────────────────
LEVEL_WIDTH  = 3840   # 3× screen width
LEVEL_HEIGHT = SCREEN_HEIGHT


def build_demo_level() -> "Level":
    """Factory: construct and return the demo level."""
    return Level()


class Level:
    """
    Container for all static geometry and initial entity spawns.

    Attributes
    ----------
    platforms    : list[Platform]
    enemies      : list[Zombie]
    width        : int
    height       : int
    player_spawn : (int, int)
    """

    def __init__(self):
        self.width  = LEVEL_WIDTH
        self.height = LEVEL_HEIGHT

        self.platforms: list = []
        self.enemies:   list = []

        # Spawn point for the player (world-space top-left)
        self.player_spawn = (100, SCREEN_HEIGHT - 200)

        self._build_geometry()
        self._spawn_enemies()

    # ── Geometry ─────────────────────────────────────────────────────────────
    def _build_geometry(self) -> None:
        P = self.platforms.append   # alias for readability
        H = SCREEN_HEIGHT

        # Ground baseline (full width, slightly below screen bottom)
        P(Platform(0,    H - 40, LEVEL_WIDTH, 60,  (60, 55, 80)))

        # ── Section 1: gentle intro ──────────────────────────────────────────
        P(Platform(250,  H - 160, 200, 20))
        P(Platform(520,  H - 240, 160, 20))
        P(Platform(740,  H - 180, 220, 20))

        # ── Section 2: tall pillar gap ───────────────────────────────────────
        P(Platform(1000, H - 300, 140, 20))
        P(Platform(1200, H - 200, 300, 20))
        P(Platform(1300, H - 380, 160, 20))

        # ── Section 3: staircase ─────────────────────────────────────────────
        for i in range(5):
            P(Platform(1620 + i * 150, H - 180 - i * 80, 120, 20))

        # ── Section 4: floating islands ──────────────────────────────────────
        P(Platform(2400, H - 200, 260, 20))
        P(Platform(2720, H - 300, 180, 20))
        P(Platform(2960, H - 200, 240, 20))

        # ── Section 5: final challenge ───────────────────────────────────────
        P(Platform(3200, H - 260, 120, 20))
        P(Platform(3380, H - 340, 120, 20))
        P(Platform(3560, H - 200, 200, 20))

        # Left & right invisible walls (keep player inside)
        P(Platform(-60,  0, 60, LEVEL_HEIGHT, (0, 0, 0)))
        P(Platform(LEVEL_WIDTH, 0, 60, LEVEL_HEIGHT, (0, 0, 0)))

    # ── Enemy spawns ─────────────────────────────────────────────────────────
    def _spawn_enemies(self) -> None:
        H = SCREEN_HEIGHT
        spawns = [
            (900,  H - 90),    # near first gap
            (1900, H - 90),    # mid staircase area
            (2850, H - 90),    # floating island section
        ]
        for x, y in spawns:
            self.enemies.append(Zombie(x, y))

    # ── Draw ─────────────────────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface, camera) -> None:
        for platform in self.platforms:
            platform.draw(surface, camera)
