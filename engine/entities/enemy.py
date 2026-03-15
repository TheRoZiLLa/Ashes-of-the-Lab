"""
enemy.py - Zombie enemy entity.

The Zombie is driven by ZombieAI (FSM) located in ai_system.py.
It tracks its own physics, health, and knockback stun state.
"""

import pygame
from engine.entities.entity_base import Entity
from engine.systems.health_system import HealthComponent
from engine.systems.ai_system import ZombieAI
from engine.physics.physics_engine import PhysicsEngine
from engine.core.timer import Timer
from engine.ui.health_bar import draw_health_bar
from engine.settings import (
    ZOMBIE_WIDTH, ZOMBIE_HEIGHT, ZOMBIE_COLOR,
    ZOMBIE_MAX_HP, ZOMBIE_KNOCKBACK_DURATION,
)


class Zombie(Entity):
    """
    Zombie enemy entity.

    Parameters
    ----------
    x, y : Spawn position (top-left of bounding box).
    """

    def __init__(self, x: float, y: float):
        super().__init__(x, y, ZOMBIE_WIDTH, ZOMBIE_HEIGHT, ZOMBIE_COLOR)

        self.health  = HealthComponent(ZOMBIE_MAX_HP)
        self.physics = PhysicsEngine()
        self.ai      = ZombieAI(self)
        self.facing  = -1   # faces left by default

        self._knockback_timer = Timer(ZOMBIE_KNOCKBACK_DURATION)

    # ── Public API ───────────────────────────────────────────────────────────
    def receive_knockback(self) -> None:
        """Called by the combat system when this enemy is hit."""
        self._knockback_timer.reset()

    @property
    def is_stunned(self) -> bool:
        return not self._knockback_timer.expired

    def die(self) -> None:
        self.dead = True

    # ── Update ───────────────────────────────────────────────────────────────
    def update(self, dt: float, player, platforms: list) -> None:
        self._knockback_timer.update(dt)

        # Let AI drive velocity (unless in knockback stun)
        self.ai.update(dt, player)

        # Resolve physics
        obstacle_rects = [p.rect for p in platforms]
        result = self.physics.step(self.rect, self.velocity, obstacle_rects, dt)
        self.sync_rect()

        if result.bottom:
            self.velocity[1] = 0
        if result.left or result.right:
            self.velocity[0] = 0

    # ── Draw ─────────────────────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface, camera) -> None:
        screen_rect = camera.apply(self.rect)

        # Flash red briefly when in knockback stun
        if self.is_stunned:
            col = (220, 80, 80)
        else:
            col = self.color

        pygame.draw.rect(surface, col, screen_rect)

        # Simple "face" lines so orientation is readable
        # Eyes
        eye_offset = 5 if self.facing > 0 else -5
        eye_x = screen_rect.centerx + eye_offset
        pygame.draw.circle(surface, (20, 20, 20), (eye_x, screen_rect.top + 10), 3)

        # Mouth (angry straight line)
        mouth_y = screen_rect.top + 20
        pygame.draw.line(
            surface, (20, 20, 20),
            (screen_rect.centerx - 6, mouth_y),
            (screen_rect.centerx + 6, mouth_y), 2
        )

        # Health bar
        draw_health_bar(surface, camera, self)
